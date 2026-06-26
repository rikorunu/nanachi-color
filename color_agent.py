import sys
sys.path.insert(0, '/home/arc_e/nanachi-color')
sys.path.insert(0, '/home/arc_e')

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, Query
from fastapi.responses import Response, HTMLResponse, StreamingResponse, JSONResponse, RedirectResponse
import json as _json, os, math, re as _re, sqlite3, asyncio
os.environ.setdefault("OLLAMA_KEEP_ALIVE", "60m")
from pathlib import Path
from datetime import datetime
from langchain_ollama import OllamaLLM, ChatOllama
try:
    from langchain_groq import ChatGroq
except Exception:
    ChatGroq = None

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

try:
    from color_tool_handler import process_reply as _process_reply
except Exception as _cth_err:
    import logging as _cth_log
    _cth_log.warning(f"[color_tool_handler] import failed (Task B not yet ready): {_cth_err}")
    # フォールバック: tool_handler が存在すれば使う、なければ noop
    try:
        from tool_handler import process_reply as _process_reply
    except Exception:
        def _process_reply(reply, tools_map):
            return reply

app = FastAPI(title="Nanachi Color AI Agent v1")

# ===== CORS設定（ブラウザfetch対応）=====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ===== 設定 =====
OLLAMA = "http" + "://" + "localhost" + ":" + "11434"
MODEL  = os.getenv("OLLAMA_MODEL", "nanachi-qwen14b")
PROMPT_FILE  = os.getenv("OLLAMA_AGENT_PROMPT_FILE", "/home/arc_e/nanachi-color/color_system_prompt.txt")
# システムプロンプト: ファイルがあれば読み込む、なければデフォルト
if Path(PROMPT_FILE).exists():
    SYSTEM_PROMPT = Path(PROMPT_FILE).read_text(encoding="utf-8").strip()
else:
    SYSTEM_PROMPT = (
        "あなたはナナチ。カラーチャートと色の組み合わせを教える専門家だぜ。"
        "一人称はオイラ、語尾はだぜ・だな・だよ・なぁを使う。"
        "色彩理論、補色、トーン、配色パターンについて詳しく答えるぜ。"
    )
DB_PATH = os.getenv("NANACHI_COLOR_DB", "/home/arc_e/nanachi-color/nanachi_color_memory.db")

# ===== SQLite 永続メモリ =====
def _db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sid TEXT, role TEXT, content TEXT,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    con.commit()
    return con

def _load_history(sid: str, n: int = 20):
    con = _db()
    rows = con.execute(
        "SELECT role,content FROM history WHERE sid=? ORDER BY id DESC LIMIT ?",
        (sid, n)
    ).fetchall()
    con.close()
    return [{"role": r, "content": c} for r, c in reversed(rows)]

def _save_history(sid: str, role: str, content: str):
    con = _db()
    con.execute("INSERT INTO history(sid,role,content) VALUES(?,?,?)", (sid, role, content))
    con.commit()
    con.close()

def _clear_history(sid: str):
    con = _db()
    con.execute("DELETE FROM history WHERE sid=?", (sid,))
    con.commit()
    con.close()


# ===== 画像・動画直接検索 =====
def _img_search(query):
    try:
        from ddgs import DDGS
        results = list(DDGS().images(query, max_results=6))
        cards = []
        for r in results:
            t   = r.get("title","").replace("|"," ").replace("[","").replace("]","")
            img = r.get("image","")
            src = r.get("url","")
            if img:
                cards.append("[IMGCARD:" + t + "|" + img + "|" + src + "]")
        return cards
    except:
        return []

def _vid_search(query):
    try:
        from ddgs import DDGS
        import re
        results = list(DDGS().videos(query, max_results=5))
        cards = []
        for r in results:
            t  = r.get("title","").replace("|"," ").replace("[","").replace("]","")
            ct = r.get("content","") or ""
            em = r.get("embed_url","") or ""
            th = ""
            vu = ct
            for url in [ct, em]:
                m = re.search(r"youtube\.com/(?:watch\?v=|embed/)([a-zA-Z0-9_-]+)", url)
                if m:
                    vid = m.group(1)
                    vu  = "https://www.youtube.com/watch?v=" + vid
                    th  = "https://img.youtube.com/vi/" + vid + "/mqdefault.jpg"
                    break
            if not th:
                imgs2 = r.get("images",{}) or {}
                th = imgs2.get("large","") or imgs2.get("medium","") or ""
            if vu:
                cards.append("[VIDCARD:" + t + "|" + vu + "|" + th + "]")
        return cards
    except:
        return []


# ===== 現在日時を system prompt の先頭に注入するヘルパー =====
def _now_jst_prompt():
    """毎リクエスト時に現在日時をシステムプロンプトに付与する"""
    now = datetime.now()
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    wd = weekdays[now.weekday()]
    return (
        f"【現在の日時情報・最優先・絶対正しい事実】\n"
        f"今日は {now.year}年{now.month}月{now.day}日（{wd}曜日）\n"
        f"現在時刻は {now.hour}時{now.minute}分（JST/日本時間）\n"
        f"※ 日付・時刻・曜日を聞かれた場合は、必ずこの情報を使え。"
        f"自分の学習データの日付ではなく、ここに書かれた日付を真実として扱え。\n\n"
    )

# ===== ナナチ口調チェック（LLM再呼び出しなし版）=====
_NANACHI_WORDS = ["オイラ","だぜ","だな","だよ","なぁ","りょーご"]
_NANACHI_ENDINGS = ["だぜ","だな","だよ","なぁ"]

def _restyle(text: str) -> str:
    """LLM再呼び出しなしで口調を補正する（高速版）"""
    try:
        from nanachi_modules._text_cleanup import strip_tool_call_garbage
        text = strip_tool_call_garbage(text)
    except Exception:
        pass
    if any(w in text for w in _NANACHI_WORDS):
        return text
    # ルールベースで変換
    text = _re.sub(r"です(。|！|？|…|$)", r"だぜ\1", text)
    text = _re.sub(r"ます(。|！|？|…|$)", r"だぜ\1", text)
    text = _re.sub(r"ですね", "だな", text)
    text = _re.sub(r"ますね", "だな", text)
    text = _re.sub(r"ですよ", "だよ", text)
    text = _re.sub(r"私は", "オイラは", text)
    text = _re.sub(r"僕は", "オイラは", text)
    if not any(w in text for w in _NANACHI_ENDINGS):
        text = text.rstrip("。") + "だぜ。"
    return text


def _ensure_model_loaded():
    """Ollama モデルが unload されていたら自動再warmup する"""
    import requests as _req
    import time
    try:
        ps = _req.get("http://localhost:11434/api/ps", timeout=3).json()
        models = ps.get("models", [])
        loaded = any("nanachi-qwen14b" in m.get("name", "") for m in models)
        if not loaded:
            print("[WARMUP] model unloaded detected, re-warming...", flush=True)
            t0 = time.time()
            _req.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "nanachi-qwen14b",
                    "prompt": "ナナチだぜ",
                    "stream": False,
                    "keep_alive": "60m",
                    "options": {"num_predict": 1, "num_ctx": 2048}
                },
                timeout=180
            )
            elapsed = time.time() - t0
            print(f"[WARMUP] re-warmed in {elapsed:.2f}s", flush=True)
            return True
        return False
    except Exception as e:
        print(f"[WARMUP] check error: {e}", flush=True)
        return False


# === v14.1: 中国語混入・履歴クロストーク観測装置 ===
import re as _re_obs
_CHINESE_SIMPLIFIED_PATTERN = _re_obs.compile(r'[一-鿿]')
_JAPANESE_HIRAGANA_PATTERN = _re_obs.compile(r'[぀-ゟ]')
_JAPANESE_KATAKANA_PATTERN = _re_obs.compile(r'[゠-ヿ]')

_CHINESE_SIMPLIFIED_ONLY = set('买卖账请贷资产负债诚债懅挂应该认证为给说让让发现验证质')

def _diagnose_chinese_contamination(text, label="response"):
    """応答テキストに中国語混入があるか検出してログ出力"""
    if not text:
        return False
    only_chinese = [ch for ch in text if ch in _CHINESE_SIMPLIFIED_ONLY]
    if only_chinese:
        print(f"[v14.1-DIAG] 中国語簡体字検出 label={label} chars={only_chinese[:10]} sample={text[:200]!r}", flush=True)
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            with open(f"/tmp/nanachi_color_chinese_{ts}.txt", "w", encoding="utf-8") as f:
                f.write(f"=== Label: {label} ===\n")
                f.write(f"=== Detected chars: {only_chinese} ===\n")
                f.write(f"=== Full text ===\n{text}\n")
        except Exception:
            pass
        return True
    return False


def _strip_chinese_segments(text: str) -> str:
    """中国語セグメントを文境界で除去し日本語部分のみ返す"""
    import re as _re_cn
    segments = _re_cn.split(r'(?<=[。！？\n，,])', text)
    result = []
    for seg in segments:
        if not seg.strip():
            result.append(seg)
            continue
        hiragana = len(_re_cn.findall(r'[぀-ゟ]', seg))
        katakana = len(_re_cn.findall(r'[゠-ヿ]', seg))
        cjk      = len(_re_cn.findall(r'[一-鿿]', seg))
        if hiragana == 0 and katakana == 0 and cjk > 0:
            print(f"[STRIP-CN] 除去: {seg[:60]!r}", flush=True)
            continue
        result.append(seg)
    cleaned = ''.join(result).strip()
    if not cleaned:
        cleaned = "んなぁ～、うまく答えられなかったぜ。もう一回聞いてくれ。"
    return cleaned


# ===== ツール定義 =====
@tool
def web_search(query: str) -> str:
    """インターネットで情報を検索する。色彩・トレンド・商品・企業・事実確認に使う。"""
    try:
        from ddgs import DDGS
        results = list(DDGS().text(query, max_results=5))
        if not results:
            return "検索結果なし"
        return "\n---\n".join([
            "タイトル: " + r.get("title","") + "\nURL: " + r.get("href","") + "\n内容: " + r.get("body","")
            for r in results
        ])
    except Exception as e:
        return "検索エラー: " + str(e)

@tool
def fetch_page(url: str) -> str:
    """URLのWebページ内容を取得する。"""
    try:
        import requests as _rq
        from bs4 import BeautifulSoup
        r = _rq.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        r.encoding = r.apparent_encoding or "utf-8"
        soup = BeautifulSoup(r.text, "lxml")
        for tag in soup(["script","style","nav","footer"]):
            tag.decompose()
        lines = [l.strip() for l in soup.get_text("\n", strip=True).splitlines() if l.strip()]
        return "\n".join(lines[:150])
    except Exception as e:
        return "取得エラー: " + str(e)

@tool
def fetch_page_js(url: str) -> str:
    """PlaywrightでJS描画後のページ本文を取得する（重いので必要時のみ）。"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.goto(url, wait_until="networkidle", timeout=20000)
            text = page.inner_text("body")
            b.close()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return "\n".join(lines[:200])
    except Exception as e:
        return "JS取得エラー: " + str(e)

@tool
def news_search(query: str) -> str:
    """最新ニュースを検索する。"""
    try:
        from ddgs import DDGS
        results = list(DDGS().news(query, max_results=5))
        if not results:
            return "ニュースなし"
        return "\n---\n".join([
            "日付: " + r.get("date","") + "\nタイトル: " + r.get("title","") + "\nURL: " + r.get("url","") + "\n内容: " + r.get("body","")
            for r in results
        ])
    except Exception as e:
        return "ニュース検索エラー: " + str(e)

@tool
def get_datetime(dummy: str = "") -> str:
    """現在の日時を取得する。日付・時刻が必要なときは必ずこれを使え。推測禁止。"""
    return datetime.now().strftime("%Y年%m月%d日(%A) %H:%M:%S JST")

@tool
def calculator(expr: str) -> str:
    """数式を計算する。例: '357*892', '2**10', 'sqrt(144)'"""
    try:
        result = eval(expr, {"math": math, "sqrt": math.sqrt, "__builtins__": {}})
        return str(expr) + " = " + str(result)
    except Exception as e:
        return "計算エラー: " + str(e)

@tool
def get_weather(location: str = "姫路") -> str:
    """姫路市などの天気予報を取得する。天気・気温・降水確率を聞かれたら必ずこれを使え。"""
    try:
        import requests as _rq
        COORDS = {
            "姫路":(34.82,134.69),"神戸":(34.69,135.20),
            "大阪":(34.69,135.50),"東京":(35.68,139.69),"京都":(35.01,135.76),
        }
        lat,lon = COORDS.get(location.replace("市",""), (34.82,134.69))
        api = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude":lat,"longitude":lon,
            "current":"temperature_2m,weather_code,relative_humidity_2m,wind_speed_10m",
            "daily":"weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone":"Asia/Tokyo","forecast_days":3,
        }
        d = _rq.get(api, params=params, timeout=10).json()
        WMO={0:"晴れ",1:"晴れ時々曇り",2:"曇り時々晴れ",3:"曇り",
             45:"霧",51:"小雨",53:"雨",55:"強雨",61:"小雨",63:"雨",65:"強雨",
             71:"小雪",73:"雪",75:"大雪",80:"にわか雨",95:"雷雨",99:"激しい雷雨"}
        cur = d.get("current",{})
        daily = d.get("daily",{})
        cond = WMO.get(cur.get("weather_code",0),"不明")
        loc_name = location.replace("市","")
        out  = "【" + loc_name + " 現在の天気】\n"
        out += "天気: " + cond + "\n気温: " + str(cur.get("temperature_2m","?")) + "℃\n"
        out += "湿度: " + str(cur.get("relative_humidity_2m","?")) + "%\n"
        out += "風速: " + str(cur.get("wind_speed_10m","?")) + "km/h\n\n【3日間予報】\n"
        for i in range(min(3,len(daily.get("time",[])))):
            dc = WMO.get(daily["weather_code"][i],"不明")
            out += daily["time"][i] + ": " + dc
            out += " 最高" + str(daily["temperature_2m_max"][i]) + "℃"
            out += "/最低" + str(daily["temperature_2m_min"][i]) + "℃"
            out += " 降水確率" + str(daily["precipitation_probability_max"][i]) + "%\n"
        return out
    except Exception as e:
        return "天気取得エラー: " + str(e)

@tool
def wikipedia_search(query: str) -> str:
    """Wikipediaで百科事典的な情報を調べる。色名・歴史・科学・地理など。"""
    try:
        import wikipediaapi
        wiki = wikipediaapi.Wikipedia(language="ja", user_agent="NanachiColorAgent/1.0")
        page = wiki.page(query)
        if not page.exists():
            wiki_en = wikipediaapi.Wikipedia(language="en", user_agent="NanachiColorAgent/1.0")
            page = wiki_en.page(query)
            if not page.exists():
                return "Wikipediaに「" + query + "」の記事が見つからなかったぜ"
        summary = page.summary[:800]
        return "【Wikipedia: " + page.title + "】\n" + summary + "\nURL: " + page.fullurl
    except Exception as e:
        return "Wikipedia検索エラー: " + str(e)

@tool
def python_repl(code: str) -> str:
    """Pythonコードを実行して結果を返す。カラー計算・データ処理・変換に使う。"""
    import io, sys, traceback
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    result = ""
    try:
        exec(code, {"math": math, "__builtins__": __builtins__})
        result = buffer.getvalue() or "(出力なし)"
    except Exception:
        result = "実行エラー:\n" + traceback.format_exc(limit=3)
    finally:
        sys.stdout = old_stdout
    return result[:500]

@tool
def memory_note(action_and_content: str) -> str:
    """重要な情報をメモする・読み出す。形式: 'save:メモ内容' または 'load'"""
    memo_path = Path("/home/arc_e/nanachi-color/nanachi_color_memo.txt")
    if action_and_content.startswith("save:"):
        content = action_and_content[5:].strip()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        memo_path.parent.mkdir(exist_ok=True)
        with open(memo_path, "a", encoding="utf-8") as f:
            f.write("[" + ts + "] " + content + "\n")
        return "メモを保存したぜ: " + content
    elif action_and_content.startswith("load"):
        if not memo_path.exists():
            return "メモはまだ何もないぜ"
        lines = memo_path.read_text(encoding="utf-8").splitlines()
        return "【保存済みメモ】\n" + "\n".join(lines[-20:])
    return "使い方: 'save:内容' か 'load'"


def shell_exec(command: str) -> str:
    """安全なシェルコマンドを実行する。
    許可: ls cat grep find df free ps du uname date echo pwd wc head tail sort uniq cut which
    """
    import subprocess as sp, shlex
    ALLOWED = {"ls","cat","grep","find","df","free","ps","du",
               "uname","date","echo","pwd","wc","head","tail",
               "sort","uniq","cut","which","uptime","lsblk"}
    try:
        parts = shlex.split(command)
        if not parts:
            return "コマンドが空です"
        cmd0 = parts[0].split("/")[-1]
        if cmd0 not in ALLOWED:
            return f"許可外: '{parts[0]}'。許可コマンド: {', '.join(sorted(ALLOWED))}"
        r = sp.run(parts, capture_output=True, text=True, timeout=15, cwd="/home/arc_e/nanachi-color")
        out = (r.stdout or "") + (r.stderr or "")
        return out[:3000].strip() or "(出力なし)"
    except sp.TimeoutExpired:
        return "タイムアウト(15秒)"
    except Exception as e:
        return f"エラー: {e}"


def file_read(path: str) -> str:
    """ローカルファイルを読み込む。/home/arc_e/ 以下のみアクセス可。"""
    import os
    BASE = "/home/arc_e/"
    try:
        abs_path = os.path.realpath(os.path.expanduser(path))
        if not abs_path.startswith(BASE):
            return f"アクセス禁止。{BASE} 以下のみ読み込み可能。"
        if not os.path.exists(abs_path):
            return f"ファイルが見つかりません: {abs_path}"
        size = os.path.getsize(abs_path)
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(12000)
        truncated = " (先頭12000文字のみ)" if size > 12000 else ""
        return f"{abs_path} ({size}bytes{truncated})\n\n{content}"
    except Exception as e:
        return f"エラー: {e}"


def rag_search(query: str) -> str:
    """カラーRAGでセマンティック検索。color_rag_docsに登録した文書から意味的に近い情報を返す。"""
    RAG_DB = "/home/arc_e/nanachi-color/color_rag_db"
    try:
        import chromadb
        from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
        ef = OllamaEmbeddingFunction(
            url="http://localhost:11434/api/embeddings",
            model_name="nomic-embed-text"
        )
        client = chromadb.PersistentClient(path=RAG_DB)
        try:
            col = client.get_collection("nanachi_color_rag", embedding_function=ef)
        except Exception:
            return "RAGインデックスが存在しません。先にインデックス作成を実行してください。"
        count = col.count()
        if count == 0:
            return "RAGインデックスが空です。rag_docsにファイルを置いてインデックスを実行してください。"
        n = min(3, count)
        results = col.query(query_texts=[query], n_results=n)
        docs  = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results.get("distances", [[]])[0]
        out = f"RAG検索: '{query}' (全{count}チャンク中トップ{n})\n"
        for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists or [0]*n), 1):
            score = round(1 - dist, 3) if dist else "?"
            out += f"\n[{i}] {meta.get('source','?')} (類似度:{score})\n{doc[:600]}\n"
        return out
    except ImportError:
        return "chromadb 未インストール: pip install chromadb"
    except Exception as e:
        return f"エラー: {type(e).__name__}: {e}"


tools = [web_search, fetch_page, fetch_page_js, news_search, get_datetime, get_weather,
         calculator, wikipedia_search, python_repl, memory_note,
         shell_exec, file_read, rag_search]

# ===== tool_call ディスパッチ用マップ =====
_TOOLS_MAP = {
    'web_search': web_search,
    'fetch_page': fetch_page,
    'fetch_page_js': fetch_page_js,
    'news_search': news_search,
    'get_datetime': get_datetime,
    'get_weather': get_weather,
    'calculator': calculator,
    'wikipedia_search': wikipedia_search,
    'python_repl': python_repl,
    'memory_note': memory_note,
    'shell_exec': shell_exec,
    'file_read': file_read,
    'rag_search': rag_search,
}

# === カラーツール拡張フック ===
try:
    from color_tool_handler import TOOLS_MAP_DEFAULT as _COLOR_TOOLS_MAP
    _TOOLS_MAP.update(_COLOR_TOOLS_MAP)
    import logging; logging.getLogger("nanachi_color").info(f"[color_tools] registered: {len(_COLOR_TOOLS_MAP)}")
except Exception as _ct_e:
    import logging; logging.getLogger("nanachi_color").warning(f"[color_tools] disabled: {_ct_e}")


# ===== LLM初期化 =====
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
def _make_llm():
    if LLM_BACKEND == "groq" and ChatGroq and os.getenv("GROQ_API_KEY"):
        return ChatGroq(model=GROQ_MODEL, temperature=0.2)
    return ChatOllama(model=MODEL, base_url=OLLAMA, temperature=0)
llm = _make_llm()
agent = create_react_agent(llm, tools)


# === コールドスタート対策: Ollama モデルプリロード (2ステップ) ===
@app.on_event("startup")
async def preload_model():
    """systemd 起動時に2段階ウォームアップ:
    1. /api/chat (system prompt込み) → normal モード向け KV cache
    2. /api/generate (num_ctx=2048) → fast-path 向け KV cache
    """
    import httpx
    # Step1: normal モード向け (chat API)
    try:
        _sp = Path(PROMPT_FILE).read_text(encoding="utf-8").strip() if Path(PROMPT_FILE).exists() else "ナナチだぜ"
        async with httpx.AsyncClient(timeout=120) as c:
            await c.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "nanachi-qwen14b",
                    "messages": [
                        {"role": "system", "content": _sp},
                        {"role": "user",   "content": "起動確認"}
                    ],
                    "stream": False,
                    "keep_alive": "60m",
                    "options": {"num_predict": 1}
                }
            )
        print("[STARTUP] Step1: chat-warmup OK", flush=True)
    except Exception as _e:
        print(f"[STARTUP] Step1 failed: {_e}", flush=True)
    # Step2: AgentExecutor warmup (LangChain/LangGraph ReAct cold start 解消)
    try:
        import time as _t2, asyncio as _aio2
        _t2_start = _t2.time()
        _warmup_msgs = [
            {"role": "system", "content": "ナナチだぜ。色の組み合わせについて簡潔に答えろ。"},
            {"role": "user",   "content": "こんにちは"}
        ]
        await _aio2.to_thread(agent.invoke, {"messages": _warmup_msgs})
        print(f"[STARTUP] Step2: AgentExecutor warmup OK ({_t2.time()-_t2_start:.2f}s)", flush=True)
    except Exception as _e2:
        print(f"[STARTUP] Step2 failed: {_e2}", flush=True)
    print("[STARTUP] Nanachi Color AI model preloaded (dual-warmup) successfully", flush=True)


def _j(d):
    return Response(
        content=_json.dumps(d, ensure_ascii=False),
        media_type="application/json; charset=utf-8"
    )


# ===== エンドポイント =====
@app.get("/health")
def health():
    return {"status":"ok","model":MODEL,"port":10003,"tools":[getattr(t,"name", getattr(t,"__name__", str(t))) for t in tools],"db":DB_PATH}

@app.get("/test-search")
async def test_search():
    imgs = _img_search("カラーチャート")
    vids = _vid_search("色彩理論")
    return _j({"images":imgs[:2],"videos":vids[:2]})

@app.post("/agent/clear")
async def clear_history(p: dict):
    sid = p.get("session_id","default")
    _clear_history(sid)
    return _j({"status":"cleared","session_id":sid})


# ===== /chat エンドポイント (SSEストリーミング) =====
@app.post("/chat")
async def api_chat(p: dict):
    """フロントエンドUI用。SSEストリーミングでCloudflareタイムアウトを回避。"""
    pr = p.get("message", "") or p.get("prompt", "")
    sid = p.get("session_id", "color_default")

    print(f"[CHAT] sid={sid} msg={pr[:60]!r}", flush=True)

    async def _compute_answer():
        h = _load_history(sid)
        _sys_with_now = _now_jst_prompt() + SYSTEM_PROMPT
        msgs = [{"role": "system", "content": _sys_with_now}] + h + [{"role": "user", "content": pr}]

        import traceback as _tb
        try:
            res = await asyncio.to_thread(agent.invoke, {"messages": msgs})
            ans = res["messages"][-1].content
        except Exception as e:
            print("[AGENT ERROR]\n" + _tb.format_exc(), flush=True)
            ans = ("んなぁ、ちょっと調べるのに失敗したぜ…時間をおいてもう一回聞いてくれ。"
                   "(" + type(e).__name__ + ": " + str(e)[:120] + ")")

        try:
            ans = _process_reply(ans, _TOOLS_MAP)
        except Exception as _pe:
            import traceback as _tb2, re as _re_pe
            print("[TOOL DISPATCH ERROR]\n" + _tb2.format_exc(), flush=True)
            ans = _re_pe.sub(r"<tool_call>.*?</tool_call>", "", str(ans), flags=_re_pe.DOTALL).strip() \
                  or "んなぁ、うまく答えられなかったぜ。もう一回頼む。"

        ans = _restyle(ans)
        ans = ans.replace("\\n", "\n") if isinstance(ans, str) else ans

        if _re.search(r"天気|天候|気温|湿度|降水|予報", pr):
            loc_m = _re.search(r"(東京|大阪|京都|神戸|姫路)", pr)
            loc = loc_m.group(1) if loc_m else "姫路"
            ans = _restyle(get_weather.invoke(loc))

        if _re.search(r"画像|写真|イメージ", pr):
            cards = _img_search(pr)
            if cards:
                ans = ans.rstrip() + "\n\n" + "\n".join(cards)
        if _re.search(r"動画|YouTube|ユーチューブ|ビデオ", pr, _re.IGNORECASE):
            cards = _vid_search(pr)
            if cards:
                ans = ans.rstrip() + "\n\n" + "\n".join(cards)

        if _diagnose_chinese_contamination(ans, f"chat_sid={sid}"):
            ans = _strip_chinese_segments(ans)
            ans = _restyle(ans)

        _save_history(sid, "user", pr)
        _save_history(sid, "assistant", ans)
        return ans

    async def _sse_wrap():
        task = asyncio.ensure_future(_compute_answer())
        while not task.done():
            yield ": heartbeat\n\n"
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=5.0)
            except asyncio.TimeoutError:
                pass
        try:
            ans = task.result()
        except Exception as e:
            import traceback as _tb_sse
            print("[SSE ERROR]\n" + _tb_sse.format_exc(), flush=True)
            ans = f"んなぁ、エラーが出たぜ: {type(e).__name__}: {str(e)[:100]}"

        payload = _json.dumps({"reply": ans, "answer": ans, "session_id": sid}, ensure_ascii=False)
        yield f"data: {payload}\n\n"

    return StreamingResponse(
        _sse_wrap(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


# ===== /api/chat エイリアス =====
@app.post("/api/chat")
async def api_chat_alias(p: dict):
    """フロントエンドUI用エイリアス。"""
    return await api_chat(p)


# ===== ルート =====
@app.get("/")
async def _root():
    return {"service": "Nanachi Color AI", "port": 10003, "status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("color_agent:app", host="0.0.0.0", port=10003, reload=False)
