"""
color_tool_handler.py
ナナチカラーAI — カラーツール群 (Task B)
"""

import re
import json
import math
import random
from typing import List, Dict, Any, Optional

# ============================================================
# 色名辞書 (60色以上)
# ============================================================

COLOR_DICT = [
    # 日本の伝統色
    {"name_jp": "桜色",   "name_en": "sakura pink",     "hex": "#FDDDE6"},
    {"name_jp": "牡丹色", "name_en": "peony",            "hex": "#E03E6E"},
    {"name_jp": "紅梅",   "name_en": "red plum",         "hex": "#E36880"},
    {"name_jp": "朱色",   "name_en": "vermillion",       "hex": "#E55B3C"},
    {"name_jp": "橙色",   "name_en": "orange",           "hex": "#EF810A"},
    {"name_jp": "山吹色", "name_en": "golden yellow",    "hex": "#F9A825"},
    {"name_jp": "金色",   "name_en": "gold",             "hex": "#FFD700"},
    {"name_jp": "黄緑",   "name_en": "yellow-green",     "hex": "#9ACD32"},
    {"name_jp": "萌黄",   "name_en": "moegi",            "hex": "#90B44B"},
    {"name_jp": "青磁色", "name_en": "celadon",          "hex": "#85C1AE"},
    {"name_jp": "群青色", "name_en": "ultramarine",      "hex": "#3333AA"},
    {"name_jp": "藍色",   "name_en": "indigo",           "hex": "#1F305E"},
    {"name_jp": "紺色",   "name_en": "navy",             "hex": "#17375E"},
    {"name_jp": "紫色",   "name_en": "purple",           "hex": "#800080"},
    {"name_jp": "桔梗色", "name_en": "bellflower",       "hex": "#6A5ACD"},
    {"name_jp": "薄紫",   "name_en": "lavender",         "hex": "#B088A0"},
    {"name_jp": "白磁",   "name_en": "white porcelain",  "hex": "#F5F0E8"},
    {"name_jp": "灰白色", "name_en": "off-white",        "hex": "#D9D9D9"},
    {"name_jp": "漆黒",   "name_en": "jet black",        "hex": "#0A0A0A"},
    {"name_jp": "墨色",   "name_en": "ink black",        "hex": "#3C3744"},
    # 基本色
    {"name_jp": "赤",     "name_en": "red",              "hex": "#FF0000"},
    {"name_jp": "緑",     "name_en": "green",            "hex": "#008000"},
    {"name_jp": "青",     "name_en": "blue",             "hex": "#0000FF"},
    {"name_jp": "黄色",   "name_en": "yellow",           "hex": "#FFFF00"},
    {"name_jp": "白",     "name_en": "white",            "hex": "#FFFFFF"},
    {"name_jp": "黒",     "name_en": "black",            "hex": "#000000"},
    {"name_jp": "灰色",   "name_en": "gray",             "hex": "#808080"},
    {"name_jp": "ピンク", "name_en": "pink",             "hex": "#FF69B4"},
    {"name_jp": "オレンジ","name_en": "orange red",      "hex": "#FF4500"},
    {"name_jp": "茶色",   "name_en": "brown",            "hex": "#8B4513"},
    # 英語系色名
    {"name_jp": "コーラル",     "name_en": "coral",       "hex": "#FF7F7F"},
    {"name_jp": "サーモン",     "name_en": "salmon",      "hex": "#FA8072"},
    {"name_jp": "ティール",     "name_en": "teal",        "hex": "#008080"},
    {"name_jp": "ミント",       "name_en": "mint",        "hex": "#98FF98"},
    {"name_jp": "ライム",       "name_en": "lime",        "hex": "#00FF00"},
    {"name_jp": "スカイブルー", "name_en": "sky blue",    "hex": "#87CEEB"},
    {"name_jp": "ネイビー",     "name_en": "navy blue",   "hex": "#000080"},
    {"name_jp": "マゼンタ",     "name_en": "magenta",     "hex": "#FF00FF"},
    {"name_jp": "シアン",       "name_en": "cyan",        "hex": "#00FFFF"},
    {"name_jp": "ターコイズ",   "name_en": "turquoise",   "hex": "#40E0D0"},
    {"name_jp": "ベージュ",     "name_en": "beige",       "hex": "#F5F5DC"},
    {"name_jp": "クリーム",     "name_en": "cream",       "hex": "#FFFDD0"},
    {"name_jp": "アイボリー",   "name_en": "ivory",       "hex": "#FFFFF0"},
    {"name_jp": "ゴールド",     "name_en": "gold",        "hex": "#FFD700"},
    {"name_jp": "シルバー",     "name_en": "silver",      "hex": "#C0C0C0"},
    {"name_jp": "バイオレット", "name_en": "violet",      "hex": "#EE82EE"},
    {"name_jp": "マルーン",     "name_en": "maroon",      "hex": "#800000"},
    {"name_jp": "オリーブ",     "name_en": "olive",       "hex": "#808000"},
    {"name_jp": "チャコール",   "name_en": "charcoal",    "hex": "#36454F"},
    {"name_jp": "ラベンダー",   "name_en": "lavender",    "hex": "#E6E6FA"},
    {"name_jp": "ペリウィンクル","name_en": "periwinkle", "hex": "#CCCCFF"},
    {"name_jp": "タン",         "name_en": "tan",         "hex": "#D2B48C"},
    {"name_jp": "カーキ",       "name_en": "khaki",       "hex": "#C3B091"},
    {"name_jp": "バーガンディ", "name_en": "burgundy",    "hex": "#800020"},
    {"name_jp": "フクシア",     "name_en": "fuchsia",     "hex": "#FF00FF"},
    {"name_jp": "インディゴ",   "name_en": "indigo",      "hex": "#4B0082"},
    {"name_jp": "エメラルド",   "name_en": "emerald",     "hex": "#50C878"},
    {"name_jp": "スカーレット", "name_en": "scarlet",     "hex": "#FF2400"},
    {"name_jp": "クリムゾン",   "name_en": "crimson",     "hex": "#DC143C"},
    {"name_jp": "アクア",       "name_en": "aqua",        "hex": "#00FFFF"},
]

# ============================================================
# 内部ユーティリティ
# ============================================================

def _parse_hex(hex_code: str) -> tuple:
    """#RRGGBB または RRGGBB を (r, g, b) に変換"""
    h = hex_code.lstrip("#")
    if len(h) != 6:
        raise ValueError(f"不正なHEXコード: {hex_code}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _to_hex(r: int, g: int, b: int) -> str:
    return "#{:02X}{:02X}{:02X}".format(
        max(0, min(255, int(round(r)))),
        max(0, min(255, int(round(g)))),
        max(0, min(255, int(round(b)))),
    )


def _rgb_to_hsl(r: int, g: int, b: int) -> dict:
    r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
    cmax = max(r_, g_, b_)
    cmin = min(r_, g_, b_)
    delta = cmax - cmin
    l = (cmax + cmin) / 2.0

    if delta == 0:
        h = 0.0
        s = 0.0
    else:
        s = delta / (1 - abs(2 * l - 1))
        if cmax == r_:
            h = 60.0 * (((g_ - b_) / delta) % 6)
        elif cmax == g_:
            h = 60.0 * (((b_ - r_) / delta) + 2)
        else:
            h = 60.0 * (((r_ - g_) / delta) + 4)

    if h < 0:
        h += 360.0
    return {"h": round(h, 1), "s": round(s * 100, 1), "l": round(l * 100, 1)}


def _hsl_to_rgb(h: float, s: float, l: float) -> tuple:
    """h: 0-360, s: 0-100, l: 0-100"""
    s /= 100.0
    l /= 100.0
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if 0 <= h < 60:
        r_, g_, b_ = c, x, 0
    elif 60 <= h < 120:
        r_, g_, b_ = x, c, 0
    elif 120 <= h < 180:
        r_, g_, b_ = 0, c, x
    elif 180 <= h < 240:
        r_, g_, b_ = 0, x, c
    elif 240 <= h < 300:
        r_, g_, b_ = x, 0, c
    else:
        r_, g_, b_ = c, 0, x
    return (
        int(round((r_ + m) * 255)),
        int(round((g_ + m) * 255)),
        int(round((b_ + m) * 255)),
    )


def _rgb_to_hsv(r: int, g: int, b: int) -> dict:
    r_, g_, b_ = r / 255.0, g / 255.0, b / 255.0
    cmax = max(r_, g_, b_)
    cmin = min(r_, g_, b_)
    delta = cmax - cmin
    v = cmax
    s = 0.0 if cmax == 0 else delta / cmax
    if delta == 0:
        h = 0.0
    elif cmax == r_:
        h = 60.0 * (((g_ - b_) / delta) % 6)
    elif cmax == g_:
        h = 60.0 * (((b_ - r_) / delta) + 2)
    else:
        h = 60.0 * (((r_ - g_) / delta) + 4)
    if h < 0:
        h += 360.0
    return {"h": round(h, 1), "s": round(s * 100, 1), "v": round(v * 100, 1)}


def _nearest_color_name(r: int, g: int, b: int) -> dict:
    """RGB空間でユークリッド距離が最も近い色名を返す"""
    best = None
    best_dist = float("inf")
    for c in COLOR_DICT:
        cr, cg, cb = _parse_hex(c["hex"])
        dist = math.sqrt((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2)
        if dist < best_dist:
            best_dist = dist
            best = c
    return best


def _color_entry(hex_code: str, role: Optional[str] = None) -> dict:
    """HEXコードから共通dictを生成"""
    hex_code = hex_code.upper()
    if not hex_code.startswith("#"):
        hex_code = "#" + hex_code
    r, g, b = _parse_hex(hex_code)
    hsl = _rgb_to_hsl(r, g, b)
    nearest = _nearest_color_name(r, g, b)
    entry = {
        "hex": hex_code,
        "rgb": {"r": r, "g": g, "b": b},
        "hsl": hsl,
        "name_jp": nearest["name_jp"],
        "name_en": nearest["name_en"],
    }
    if role is not None:
        entry["role"] = role
    return entry


def _wcag_relative_luminance(r: int, g: int, b: int) -> float:
    def linearize(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


# ============================================================
# 1. color_random_palette
# ============================================================

def color_random_palette(count: int = 5, harmony_type: str = "random") -> List[dict]:
    """
    count色のランダムパレットを生成する。
    harmony_typeに応じて色相間の関係を調整する。
    """
    count = max(3, min(7, int(count)))

    if harmony_type == "random":
        hues = [random.uniform(0, 360) for _ in range(count)]
    elif harmony_type == "analogous":
        base_h = random.uniform(0, 360)
        step = 30.0
        hues = [(base_h + i * step) % 360 for i in range(count)]
    elif harmony_type == "complementary":
        base_h = random.uniform(0, 360)
        comp_h = (base_h + 180) % 360
        pool = [base_h, comp_h]
        hues = [pool[i % 2] + random.uniform(-15, 15) for i in range(count)]
    elif harmony_type == "triadic":
        base_h = random.uniform(0, 360)
        pool = [(base_h + i * 120) % 360 for i in range(3)]
        hues = [pool[i % 3] + random.uniform(-10, 10) for i in range(count)]
    elif harmony_type == "tetradic":
        base_h = random.uniform(0, 360)
        pool = [(base_h + i * 90) % 360 for i in range(4)]
        hues = [pool[i % 4] + random.uniform(-10, 10) for i in range(count)]
    else:
        hues = [random.uniform(0, 360) for _ in range(count)]

    result = []
    for h in hues:
        h = h % 360
        s = random.uniform(40, 90)
        l = random.uniform(30, 70)
        r, g, b = _hsl_to_rgb(h, s, l)
        result.append(_color_entry(_to_hex(r, g, b)))
    return result


# ============================================================
# 2. color_harmonize
# ============================================================

def color_harmonize(base_hex: str, harmony_type: str) -> List[dict]:
    """
    base_hexを基準に harmony_type に従った配色セットを返す。
    """
    r, g, b = _parse_hex(base_hex)
    hsl = _rgb_to_hsl(r, g, b)
    h, s, l = hsl["h"], hsl["s"], hsl["l"]

    def make(hue, sat=None, lig=None, role=""):
        hue = hue % 360
        sr = sat if sat is not None else s
        lr = lig if lig is not None else l
        rr, gg, bb = _hsl_to_rgb(hue, sr, lr)
        entry = _color_entry(_to_hex(rr, gg, bb), role=role)
        return entry

    base_entry = _color_entry(base_hex, role="ベース")

    if harmony_type == "analogous":
        colors = [
            make(h - 30, role="類似色(-30°)"),
            base_entry,
            make(h + 30, role="類似色(+30°)"),
        ]
    elif harmony_type == "complementary":
        colors = [
            base_entry,
            make(h + 180, role="補色"),
        ]
    elif harmony_type == "split-complementary":
        colors = [
            base_entry,
            make(h + 150, role="分割補色1"),
            make(h + 210, role="分割補色2"),
        ]
    elif harmony_type == "triadic":
        colors = [
            base_entry,
            make(h + 120, role="三角配色2"),
            make(h + 240, role="三角配色3"),
        ]
    elif harmony_type == "tetradic":
        colors = [
            base_entry,
            make(h + 90,  role="四角配色2"),
            make(h + 180, role="四角配色3"),
            make(h + 270, role="四角配色4"),
        ]
    elif harmony_type == "monochromatic":
        colors = [
            make(h, s, max(10, l - 30),  role="暗い"),
            make(h, s, max(10, l - 15),  role="やや暗い"),
            base_entry,
            make(h, s, min(90, l + 15),  role="やや明るい"),
            make(h, s, min(90, l + 30),  role="明るい"),
        ]
    else:
        colors = [base_entry]

    return colors


# ============================================================
# 3. color_hex_info
# ============================================================

def color_hex_info(hex_code: str) -> dict:
    """
    HEXコードの詳細情報を返す。
    """
    h = hex_code.strip()
    if not h.startswith("#"):
        h = "#" + h
    h = h.upper()

    r, g, b = _parse_hex(h)
    hsl = _rgb_to_hsl(r, g, b)
    hsv = _rgb_to_hsv(r, g, b)
    nearest = _nearest_color_name(r, g, b)

    lum = _wcag_relative_luminance(r, g, b)
    brightness = "明" if lum >= 0.179 else "暗"

    hue_angle = hsl["h"]
    if (0 <= hue_angle < 30) or (330 <= hue_angle <= 360):
        warm_cool = "暖色"
    elif 30 <= hue_angle < 90:
        warm_cool = "暖色"
    elif 90 <= hue_angle < 150:
        warm_cool = "中性"
    elif 150 <= hue_angle < 270:
        warm_cool = "寒色"
    elif 270 <= hue_angle < 330:
        warm_cool = "中性"
    else:
        warm_cool = "中性"

    white_lum = 1.0
    black_lum = 0.0
    contrast_white = (white_lum + 0.05) / (lum + 0.05)
    contrast_black = (lum + 0.05) / (black_lum + 0.05)
    recommended_text_color = "#FFFFFF" if contrast_white >= contrast_black else "#000000"

    return {
        "hex": h,
        "rgb": {"r": r, "g": g, "b": b},
        "hsl": hsl,
        "hsv": hsv,
        "name_jp": nearest["name_jp"],
        "name_en": nearest["name_en"],
        "brightness": brightness,
        "warm_cool": warm_cool,
        "recommended_text_color": recommended_text_color,
    }


# ============================================================
# 4. color_name_search
# ============================================================

def color_name_search(query: str) -> List[dict]:
    """
    色名（日本語・英語）の部分一致検索。最大5件返す。
    """
    q = query.lower().strip()
    results = []
    for c in COLOR_DICT:
        if q in c["name_jp"].lower() or q in c["name_en"].lower():
            r, g, b = _parse_hex(c["hex"])
            hsl = _rgb_to_hsl(r, g, b)
            results.append({
                "hex": c["hex"].upper(),
                "name_jp": c["name_jp"],
                "name_en": c["name_en"],
                "rgb": {"r": r, "g": g, "b": b},
                "hsl": hsl,
            })
        if len(results) >= 5:
            break
    return results


# ============================================================
# 5. color_blend
# ============================================================

def color_blend(color1: str, color2: str, steps: int = 5) -> List[dict]:
    """
    2色間のグラデーション。RGB線形補間。
    steps件のリストを返す（両端含む）。
    """
    steps = max(2, int(steps))
    r1, g1, b1 = _parse_hex(color1)
    r2, g2, b2 = _parse_hex(color2)

    result = []
    for i in range(steps):
        t = i / (steps - 1)
        r = r1 + (r2 - r1) * t
        g = g1 + (g2 - g1) * t
        b = b1 + (b2 - b1) * t
        result.append(_color_entry(_to_hex(r, g, b)))
    return result


# ============================================================
# 6. color_contrast_check
# ============================================================

def color_contrast_check(foreground: str, background: str) -> dict:
    """
    WCAG 2.1準拠のコントラスト比を計算。
    """
    rf, gf, bf = _parse_hex(foreground)
    rb, gb, bb = _parse_hex(background)

    lum_f = _wcag_relative_luminance(rf, gf, bf)
    lum_b = _wcag_relative_luminance(rb, gb, bb)

    lighter = max(lum_f, lum_b)
    darker  = min(lum_f, lum_b)
    ratio = (lighter + 0.05) / (darker + 0.05)

    wcag_aa  = ratio >= 4.5
    wcag_aaa = ratio >= 7.0

    if wcag_aaa:
        readable = "非常に読みやすい（AAA合格）"
    elif wcag_aa:
        readable = "読みやすい（AA合格）"
    elif ratio >= 3.0:
        readable = "やや読みにくい（大きい文字ならAA合格）"
    else:
        readable = "読みにくい（不合格）"

    return {
        "contrast_ratio": round(ratio, 2),
        "wcag_aa":  wcag_aa,
        "wcag_aaa": wcag_aaa,
        "readable": readable,
    }


# ============================================================
# 7. color_rag_search
# ============================================================

def color_rag_search(query: str, top_k: int = 3) -> str:
    """
    ChromaDBの nanachi_color_rag コレクションを検索して整形テキストを返す。
    DBが存在しない場合はフォールバックメッセージを返す。
    """
    PERSIST_DIR = "/home/arc_e/nanachi-color/color_rag_db"
    COLLECTION_NAME = "nanachi_color_rag"

    try:
        import chromadb
        client = chromadb.PersistentClient(path=PERSIST_DIR)
        try:
            col = client.get_collection(COLLECTION_NAME)
        except Exception:
            return "カラー知識ベース未初期化（nanachi_color_ragコレクションが見つかりません）"

        results = col.query(query_texts=[query], n_results=min(top_k, col.count()))
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        if not docs:
            return f"「{query}」に関連するカラー知識は見つかりませんでした。"

        lines = [f"【カラー知識ベース検索結果: {query}】"]
        for i, (doc, meta) in enumerate(zip(docs, metas), 1):
            title = meta.get("title", f"ドキュメント{i}")
            lines.append(f"\n[{i}] {title}")
            lines.append(doc[:400] + ("..." if len(doc) > 400 else ""))
        return "\n".join(lines)

    except ImportError:
        return "カラー知識ベース未初期化（chromadbモジュールが見つかりません）"
    except Exception as e:
        return f"カラー知識ベース検索エラー: {str(e)}"


# ============================================================
# process_reply
# ============================================================

TOOL_CALL_PATTERN = re.compile(r'<tool_call>\s*(\{.*?\})\s*</tool_call>', re.DOTALL)

TOOLS_MAP_DEFAULT: Dict[str, Any] = {
    "color_random_palette":  color_random_palette,
    "color_harmonize":       color_harmonize,
    "color_hex_info":        color_hex_info,
    "color_name_search":     color_name_search,
    "color_blend":           color_blend,
    "color_contrast_check":  color_contrast_check,
    "color_rag_search":      color_rag_search,
}


def _format_tool_result(name: str, result: Any) -> str:
    """ツール結果をLLM向けのナラティブテキストに整形する"""
    if isinstance(result, str):
        return result

    if name == "color_hex_info":
        r = result
        return (
            f"【色情報: {r['hex']}】\n"
            f"色名: {r['name_jp']}（{r['name_en']}）\n"
            f"RGB: R={r['rgb']['r']}, G={r['rgb']['g']}, B={r['rgb']['b']}\n"
            f"HSL: H={r['hsl']['h']}°, S={r['hsl']['s']}%, L={r['hsl']['l']}%\n"
            f"HSV: H={r['hsv']['h']}°, S={r['hsv']['s']}%, V={r['hsv']['v']}%\n"
            f"明暗: {r['brightness']} / 色温感: {r['warm_cool']}\n"
            f"推奨テキスト色: {r['recommended_text_color']}"
        )

    if name == "color_contrast_check":
        r = result
        aa_str  = "合格" if r["wcag_aa"]  else "不合格"
        aaa_str = "合格" if r["wcag_aaa"] else "不合格"
        return (
            f"【コントラスト比】\n"
            f"比率: {r['contrast_ratio']}:1\n"
            f"WCAG AA (4.5:1): {aa_str}\n"
            f"WCAG AAA (7:1): {aaa_str}\n"
            f"判定: {r['readable']}"
        )

    if name in ("color_random_palette", "color_blend"):
        lines = [f"【{name} 結果】"]
        for i, c in enumerate(result, 1):
            lines.append(
                f"  {i}. {c['name_jp']}（{c['name_en']}）: {c['hex']}  "
                f"RGB({c['rgb']['r']},{c['rgb']['g']},{c['rgb']['b']})"
            )
        return "\n".join(lines)

    if name == "color_harmonize":
        lines = ["【配色セット】"]
        for c in result:
            role = c.get("role", "")
            lines.append(
                f"  [{role}] {c['name_jp']}（{c['name_en']}）: {c['hex']}"
            )
        return "\n".join(lines)

    if name == "color_name_search":
        if not result:
            return "該当する色名は見つかりませんでした。"
        lines = ["【色名検索結果】"]
        for c in result:
            lines.append(f"  {c['name_jp']}（{c['name_en']}）: {c['hex']}")
        return "\n".join(lines)

    # フォールバック: JSONダンプ
    try:
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception:
        return str(result)


def process_reply(reply: str, tools_map: dict) -> str:
    """
    LLM応答から <tool_call>{...}</tool_call> を検出して実行し、
    結果を整形したテキストを返す。
    ツールが見つからない場合や例外は安全にハンドルする。
    """
    merged_map = {**TOOLS_MAP_DEFAULT, **tools_map}

    def replace_tool_call(m: re.Match) -> str:
        raw = m.group(1)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as e:
            return f"[ツール呼び出しJSONパースエラー: {e}]"

        tool_name = payload.get("name") or payload.get("tool_name") or payload.get("function")
        arguments  = payload.get("arguments") or payload.get("parameters") or payload.get("args") or {}

        if not tool_name:
            return "[ツール名が見つかりません]"

        func = merged_map.get(tool_name)
        if func is None:
            return f"[未定義のツール: {tool_name}]"

        try:
            if isinstance(arguments, dict):
                result = func(**arguments)
            elif isinstance(arguments, list):
                result = func(*arguments)
            else:
                result = func(arguments)
        except Exception as e:
            return f"[ツール実行エラー ({tool_name}): {e}]"

        return _format_tool_result(tool_name, result)

    processed = TOOL_CALL_PATTERN.sub(replace_tool_call, reply)
    return processed
