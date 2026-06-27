"""
布生地在庫管理モジュール
DB: /home/arc_e/nanachi-color/fabric_inventory.db
"""
import sqlite3
import json
import base64
import os
import math
from pathlib import Path
from datetime import datetime
from typing import List, Optional

DB_PATH = "/home/arc_e/nanachi-color/fabric_inventory.db"

# Pillow は try/except で囲む
try:
    from PIL import Image
    import io as _io
    _PILLOW_AVAILABLE = True
except ImportError:
    _PILLOW_AVAILABLE = False


def _make_thumbnail_b64(image_bytes: bytes, size: int = 200, quality: int = 60) -> str:
    """画像バイト列をサムネイル(size x size JPEG)にしてBase64文字列で返す"""
    if _PILLOW_AVAILABLE and image_bytes:
        try:
            buf_in = _io.BytesIO(image_bytes)
            img = Image.open(buf_in).convert("RGB")
            img.thumbnail((size, size), Image.LANCZOS)
            buf_out = _io.BytesIO()
            img.save(buf_out, format="JPEG", quality=quality)
            return base64.b64encode(buf_out.getvalue()).decode("utf-8")
        except Exception:
            pass
    # Pillow が使えないかエラーのときはそのままBase64化
    return base64.b64encode(image_bytes).decode("utf-8") if image_bytes else ""


def _rgb_distance(rgb1: dict, rgb2: dict) -> float:
    """2色間のRGBユークリッド距離"""
    dr = rgb1.get("r", 0) - rgb2.get("r", 0)
    dg = rgb1.get("g", 0) - rgb2.get("g", 0)
    db = rgb1.get("b", 0) - rgb2.get("b", 0)
    return math.sqrt(dr * dr + dg * dg + db * db)


def _hex_to_rgb(hex_str: str) -> dict:
    """#RRGGBB → {"r":R,"g":G,"b":B}"""
    hex_str = hex_str.lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join(c * 2 for c in hex_str)
    try:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return {"r": r, "g": g, "b": b}
    except (ValueError, IndexError):
        return {"r": 0, "g": 0, "b": 0}


def _ensure_rgb(color: dict) -> dict:
    """色dictからrgbを補完（hexしかない場合に対応）"""
    rgb = color.get("rgb")
    if rgb and isinstance(rgb, dict):
        return rgb
    hex_val = color.get("hex", "")
    return _hex_to_rgb(hex_val)


class FabricInventory:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """テーブル初期化"""
        os.makedirs(str(Path(self.db_path).parent), exist_ok=True)
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fabrics (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT NOT NULL,
                    memo        TEXT DEFAULT '',
                    colors_json TEXT DEFAULT '[]',
                    image_b64   TEXT DEFAULT '',
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_fabric(
        self,
        name: str,
        image_bytes: bytes,
        colors: list,
        memo: str = "",
    ) -> int:
        """布生地を登録してIDを返す"""
        now = datetime.now().isoformat(timespec="seconds")
        thumb_b64 = _make_thumbnail_b64(image_bytes)
        colors_json = json.dumps(colors, ensure_ascii=False)
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO fabrics (name, memo, colors_json, image_b64, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, memo, colors_json, thumb_b64, now, now),
            )
            conn.commit()
            return cur.lastrowid

    def list_fabrics(self) -> List[dict]:
        """全布生地一覧を返す（image_b64は除く）"""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, memo, colors_json, created_at, updated_at FROM fabrics ORDER BY id"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_fabric(self, fabric_id: int) -> Optional[dict]:
        """IDで1件取得（image_b64含む）"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM fabrics WHERE id = ?", (fabric_id,)
            ).fetchone()
        return dict(row) if row else None

    def delete_fabric(self, fabric_id: int) -> bool:
        """布生地を削除"""
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM fabrics WHERE id = ?", (fabric_id,))
            conn.commit()
            return cur.rowcount > 0

    def find_matching_fabrics(self, target_colors: list, top_k: int = 3) -> List[dict]:
        """target_colors に色が近い布生地を top_k 件返す

        マッチング方法:
        1. 各布生地の colors_json と target_colors を比較
        2. 各target_colorに対して最も近い布生地色を見つけ、その距離を記録
        3. 全target_colorの最小距離の平均を計算
        4. 距離が小さい順に返す
        5. 各結果に matched_color（最も近いtarget_colorのhex）を付加
        """
        fabrics = self.list_fabrics()
        if not fabrics or not target_colors:
            return []

        scored = []
        for fabric in fabrics:
            fabric_colors = json.loads(fabric.get("colors_json", "[]"))
            if not fabric_colors:
                continue

            # target_colors ごとに、布生地内で最も近い色との距離を取得
            total_dist = 0.0
            best_match_hex = None
            best_match_dist = float("inf")

            for tc in target_colors:
                tc_rgb = _ensure_rgb(tc)
                min_dist = float("inf")
                for fc in fabric_colors:
                    fc_rgb = _ensure_rgb(fc)
                    d = _rgb_distance(tc_rgb, fc_rgb)
                    if d < min_dist:
                        min_dist = d
                    if d < best_match_dist:
                        best_match_dist = d
                        best_match_hex = tc.get("hex", "")
                total_dist += min_dist

            avg_dist = total_dist / len(target_colors)
            scored.append((avg_dist, best_match_hex, fabric))

        scored.sort(key=lambda x: x[0])
        results = []
        for dist, matched_hex, fabric in scored[:top_k]:
            item = dict(fabric)
            item["distance"] = round(dist, 2)
            item["matched_color"] = matched_hex
            results.append(item)
        return results

    def get_all_colors(self) -> List[dict]:
        """全布生地の色一覧を返す（配色提案用）

        Returns:
            List of {"fabric_id", "fabric_name", "hex", "name_jp", "ratio"}
        """
        fabrics = self.list_fabrics()
        result = []
        for fabric in fabrics:
            colors = json.loads(fabric.get("colors_json", "[]"))
            for c in colors:
                result.append({
                    "fabric_id":   fabric["id"],
                    "fabric_name": fabric["name"],
                    "hex":         c.get("hex", ""),
                    "name_jp":     c.get("name_jp", ""),
                    "ratio":       c.get("ratio", 0.0),
                })
        return result


# ============================================================
# ツール関数（color_tool_handler.py の TOOLS_MAP_DEFAULT に追加用）
# ============================================================

def tool_list_fabrics() -> str:
    """在庫の布生地一覧を整形テキストで返す（LLMから呼び出し用）"""
    inv = FabricInventory()
    fabrics = inv.list_fabrics()
    if not fabrics:
        return "在庫に布生地は登録されていないぜ。写真を撮って登録してくれ。"
    lines = [f"【布生地在庫一覧】({len(fabrics)}件)"]
    for f in fabrics:
        colors = json.loads(f.get("colors_json", "[]"))
        color_names = [c.get("name_jp", "?") for c in colors[:3]]
        lines.append(
            f"  ID:{f['id']} 「{f['name']}」 主な色: {', '.join(color_names)} | {f.get('memo', '')}"
        )
    return "\n".join(lines)


def tool_match_fabrics_by_color(hex_color: str, top_k: int = 3) -> str:
    """指定色に合う布生地を在庫から検索（LLMから呼び出し用）

    Args:
        hex_color: 検索する色のHEX値（例: "#FF5733"）
        top_k:     返す件数（デフォルト3）
    """
    hex_color = hex_color.strip()
    if not hex_color.startswith("#"):
        hex_color = "#" + hex_color

    rgb = _hex_to_rgb(hex_color)
    target_colors = [{"hex": hex_color, "rgb": rgb}]

    inv = FabricInventory()
    matches = inv.find_matching_fabrics(target_colors, top_k=top_k)

    if not matches:
        return f"「{hex_color}」に近い布生地は在庫に見つからなかったぜ。"

    lines = [f"【{hex_color} に近い布生地】(上位{len(matches)}件)"]
    for m in matches:
        colors = json.loads(m.get("colors_json", "[]"))
        color_names = [c.get("name_jp", "?") for c in colors[:3]]
        lines.append(
            f"  ID:{m['id']} 「{m['name']}」 色距離:{m['distance']:.1f} "
            f"| 主な色: {', '.join(color_names)} | {m.get('memo','')}"
        )
    return "\n".join(lines)


# ============================================================
# 動作確認
# ============================================================

if __name__ == "__main__":
    inv = FabricInventory()
    print("DB初期化OK:", inv.db_path)

    # ダミーデータで動作確認
    dummy_colors = [
        {
            "hex": "#FF5733",
            "rgb": {"r": 255, "g": 87, "b": 51},
            "hsl": {"h": 11, "s": 100, "l": 60},
            "name_jp": "朱色",
            "ratio": 0.6,
        }
    ]
    fid = inv.add_fabric("テスト生地", b"dummy_image", dummy_colors, "テスト用")
    print("登録ID:", fid)

    # 2件目
    dummy_colors2 = [
        {
            "hex": "#3366CC",
            "rgb": {"r": 51, "g": 102, "b": 204},
            "name_jp": "群青色",
            "ratio": 0.8,
        }
    ]
    inv.add_fabric("青系デニム", b"dummy_image2", dummy_colors2, "デニム素材")

    print("一覧:", inv.list_fabrics())
    print()
    print(tool_list_fabrics())
    print()

    # 色検索テスト
    print(tool_match_fabrics_by_color("#FF4422"))
    print()
    print(tool_match_fabrics_by_color("#2255BB"))
    print()

    # 全色一覧
    print("全色一覧:", inv.get_all_colors())

    # 削除テスト
    deleted = inv.delete_fabric(fid)
    print("削除結果:", deleted)
    print("削除後一覧:", inv.list_fabrics())
