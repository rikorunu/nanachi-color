# ナナチカラーAI 仕様書 v1.0

## 概要
ナナチ簿記AIをベースに、簿記ツール/RAGを取り除き
**カラーチャート・配色提案専門**に特化したナナチAI。

## 基本情報
- プロジェクトディレクトリ: /home/arc_e/nanachi-color/
- ポート: 10003
- ベースモデル: nanachi-qwen14b:latest（Ollama, temp 0.8）
- Embedding: nomic-embed-text:latest（768次元）
- ChromaDB collection: nanachi_color_rag
- キャラクター: メイドインアビスのナナチ（簿記AIと同一口調）

## ファイル構成

### Task A担当（color_agent.py + systemd）
- /home/arc_e/nanachi-color/color_agent.py  ← FastAPI メイン
- /home/arc_e/nanachi-color/nanachi-color.service  ← systemd サービス定義（参考テンプレ）

### Task B担当（color_tool_handler.py）
- /home/arc_e/nanachi-color/color_tool_handler.py  ← カラーツール群

### Task C担当（RAGデータ + ingest）
- /home/arc_e/nanachi-color/rag_docs/*.json  ← カラー理論ドキュメント群
- /home/arc_e/nanachi-color/ingest_color_rag.py  ← ChromaDB投入スクリプト

### Task D担当（UI + プロンプト + テスト）
- /home/arc_e/nanachi-color/color_system_prompt.txt  ← システムプロンプト
- /home/arc_e/nanachi-color/nanachi_color_ui.html  ← チャットUI
- /home/arc_e/nanachi-color/tests/test_color.py  ← テストスクリプト

---

## Task A 仕様: color_agent.py

### 要件
- /home/arc_e/ollama_agent.py をベースに「簿記専用コード」を全削除
- 残すもの: FastAPI基盤, CORS, startup warmup, ストリーミング応答, memory_db, /chat エンドポイント
- 削除するもの: bk_* 全ツール、簿記RAG、bk_lookup_rag、fastpath等の簿記ロジック
- PROMPT_FILE = "/home/arc_e/nanachi-color/color_system_prompt.txt"
- PORT = 10003
- tool_handler インポート先を color_tool_handler に変更
- startup warmup のwarmupプロンプトをカラー向けに変更

### 実装要点
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
os.environ.setdefault("OLLAMA_KEEP_ALIVE", "60m")
# from color_tool_handler import process_reply as _process_reply  (Task B完成後)
PORT = 10003
PROMPT_FILE = "/home/arc_e/nanachi-color/color_system_prompt.txt"
```

### systemd サービス (nanachi-color.service テンプレ)
```
[Unit]
Description=Nanachi Color AI Agent
After=network.target ollama.service

[Service]
Type=simple
User=arc_e
WorkingDirectory=/home/arc_e/nanachi-color
ExecStart=/home/arc_e/ollama-agent-venv/bin/uvicorn color_agent:app --host 0.0.0.0 --port 10003
Restart=always
RestartSec=10
Environment=PYTHONPATH=/home/arc_e/nanachi-color:/home/arc_e

[Install]
WantedBy=multi-user.target
```

---

## Task B 仕様: color_tool_handler.py

### 提供ツール（7種）

#### 1. color_random_palette
```
入力: count=3〜7（デフォルト5）, harmony_type="random"|"analogous"|"complementary"|"triadic"|"tetradic"
出力: 色リスト [{hex, rgb, hsl, name_jp, name_en}, ...]
```

#### 2. color_harmonize
```
入力: base_hex="#RRGGBB", harmony_type="analogous"|"complementary"|"split-complementary"|"triadic"|"tetradic"|"monochromatic"
出力: 配色リスト [{hex, rgb, hsl, name_jp, role}, ...]
```

#### 3. color_hex_info
```
入力: hex_code="#RRGGBB"
出力: {hex, rgb:{r,g,b}, hsl:{h,s,l}, hsv:{h,s,v}, name_jp, name_en, brightness, warm_cool, recommended_text_color}
```

#### 4. color_name_search
```
入力: query="桜色" または "rose"
出力: [{hex, name_jp, name_en, rgb, hsl}, ...] 最大5件
```

#### 5. color_blend
```
入力: color1="#RRGGBB", color2="#RRGGBB", steps=5
出力: グラデーション色リスト（stepsの数だけ中間色）
```

#### 6. color_contrast_check
```
入力: foreground="#RRGGBB", background="#RRGGBB"
出力: {contrast_ratio, wcag_aa, wcag_aaa, readable}  WCAG2.1準拠
```

#### 7. color_rag_search
```
入力: query="暖色系の組み合わせ", top_k=3
出力: ChromaDB nanachi_color_rag からの検索結果テキスト
```

### 色名辞書（必須収録・最低50色）
日本語伝統色名含む: 桜色,牡丹色,紅梅,朱色,橙色,山吹色,金色,黄緑,萌黄,青磁,群青,藍色,
紺色,紫色,桔梗色,薄紫,白磁,灰白,漆黒,墨色 + 英語色名（coral,salmon,teal,indigo等）

### HEX→色名マッチング方式
RGB空間でのユークリッド距離が最も近い色名を返す（厳密一致不要）

### process_reply関数
既存tool_handler.pyと同一シグネチャで実装:
```python
def process_reply(reply: str, tools_map: dict) -> str:
    # <tool_call>{"name":"color_harmonize","arguments":{...}}</tool_call> を検出・実行
```

---

## Task C 仕様: RAGドキュメント + ingest

### RAGドキュメント構成（rag_docs/配下）

#### color_theory_basics.json
```json
[
  {"id": "ct001", "title": "色の三属性", "theme": "基礎理論", "content": "色相（Hue）・彩度（Saturation）・明度（Lightness）の3要素..."},
  {"id": "ct002", "title": "色相環（12色相）", "theme": "基礎理論", "content": "..."},
  ...
]
```

#### color_harmony_rules.json（配色法則 20件以上）
- 補色配色 (Complementary): 色相環180度対面
- 類似色配色 (Analogous): 隣接する2〜3色相
- 三角配色 (Triadic): 120度間隔の3色
- 四角配色 (Tetradic/Square): 90度間隔の4色
- 分割補色 (Split-Complementary): 補色の両隣
- 単色配色 (Monochromatic): 同色相で明度差
- 暖色系 (Warm Colors): 赤・橙・黄系
- 寒色系 (Cool Colors): 青・緑・紫系
- トーンオントーン: 同色相で明度変化
- ドミナントトーン: 同トーンで色相変化
- カマイユ配色: 極めて近似した2色

#### color_psychology.json（色彩心理 15件以上）
- 赤: 情熱・エネルギー・警告
- 青: 信頼・冷静・プロフェッショナル
- 緑: 自然・安心・成長
- 黄: 明るさ・注意・楽観
- 紫: 高貴・神秘・創造性
- 橙: 活力・親しみやすさ・食欲
- 白: 清潔・シンプル・無垢
- 黒: 高級・権威・洗練
- ピンク: 優しさ・愛・フェミニン
...

#### color_usage_guide.json（用途別配色 15件以上）
- Webデザイン向け配色
- SNS・ブランディング配色
- ファッション配色
- インテリア配色
- 季節別配色（春夏秋冬）
- 和風配色
- ポップ配色
- ミニマル配色

### ingest_color_rag.py 要件
- chromadb パッケージ使用
- collection名: "nanachi_color_rag"
- persist_directory: "/home/arc_e/nanachi-color/color_rag_db"
- embedding model: nomic-embed-text (Ollama経由)
- 各ドキュメントのidはユニーク
- 実行後に投入件数を表示

---

## Task D 仕様: UI + システムプロンプト + テスト

### color_system_prompt.txt 要件

以下を必ず含める:
1. 【最優先】日本語のみ応答命令（既存と同じ）
2. ナナチキャラクター設定（既存と完全同一）
3. ユーザー情報（りょーご情報、既存と同一）
4. カラー専用ツール呼び出し義務
   - 配色を聞かれたら必ず color_harmonize を呼ぶ
   - ランダム配色を求められたら color_random_palette を呼ぶ
   - 色名・HEX情報を聞かれたら color_hex_info または color_name_search を呼ぶ
   - 配色理論を聞かれたら color_rag_search を呼ぶ
5. 応答フォーマット
   - 色は必ず「色名（#HEXコード）」形式で表示
   - 配色提案は「ベース色 + 理由」付きで表示
   - 色の視覚イメージを絵文字カラーブロックで補足（🔴🟠🟡🟢🔵🟣⚫⚪）

### nanachi_color_ui.html 要件
- 既存 /home/arc_e/ollama_chat_ui.html をベースに改修
- カラーパレット表示パネルを追加（APIレスポンスのHEXコードを検出してswatchを描画）
- "ランダム配色" ボタン追加（クリックで「ランダムな配色を5色生成して」を自動送信）
- "配色提案" エリア: ユーザーが色を入力するとcolor pickerと連動
- ヘッダーに「🎨 ナナチカラー」表記

### tests/test_color.py 要件
- color_tool_handler の全7ツールをテスト
- color_hex_info("#FF5733") → 橙系
- color_harmonize("#3498DB", "complementary") → 補色が含まれるか
- color_random_palette(count=5) → 5色返ってくるか
- color_contrast_check("#FFFFFF", "#000000") → contrast_ratio >= 21
- 全テストprintで結果を出力（pytestではなく単体実行可能）

---

## 依存関係
- Task A は Task B の完成を待って `from color_tool_handler import process_reply` をインポート
- Task C の ingest は Task B の color_rag_search が使う collection を作成
- Task D の UI は Task A が完成後に動作確認

## 完了条件
各Task: 担当ファイルを作成 → python3 -m py_compile で構文チェック → touch /home/arc_e/nanachi-color/COMPLETE_TASK_[A/B/C/D]

## 注意事項
- 既存の ollama_agent.py / tool_handler.py は一切触るな
- 既存ChromaDBコレクション（nanachi_rag, nanachi_bookkeeping_rag, nanachi_legal_rag）は一切触るな
- color_rag_db は /home/arc_e/nanachi-color/color_rag_db/ に独立して作成
