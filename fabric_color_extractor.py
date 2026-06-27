"""
fabric_color_extractor.py
布生地画像から代表色を抽出するモジュール
PIL/Pillowを使用、外部APIなし
"""
from PIL import Image
import io
import colorsys
import math
from typing import List, Dict, Any


def _rgb_to_hsl(r: int, g: int, b: int) -> Dict[str, float]:
    """RGB (0-255) → HSL (0-360, 0-100, 0-100)"""
    r_ = r / 255.0
    g_ = g / 255.0
    b_ = b / 255.0
    cmax = max(r_, g_, b_)
    cmin = min(r_, g_, b_)
    delta = cmax - cmin
    lightness = (cmax + cmin) / 2.0

    if delta == 0:
        hue = 0.0
        saturation = 0.0
    else:
        saturation = delta / (1 - abs(2 * lightness - 1))
        if cmax == r_:
            hue = 60.0 * (((g_ - b_) / delta) % 6)
        elif cmax == g_:
            hue = 60.0 * (((b_ - r_) / delta) + 2)
        else:
            hue = 60.0 * (((r_ - g_) / delta) + 4)

    if hue < 0:
        hue += 360.0

    return {
        "h": round(hue, 1),
        "s": round(saturation * 100, 1),
        "l": round(lightness * 100, 1),
    }


def _color_distance(c1: tuple, c2: tuple) -> float:
    """RGB空間ユークリッド距離"""
    return math.sqrt(
        (c1[0] - c2[0]) ** 2 +
        (c1[1] - c2[1]) ** 2 +
        (c1[2] - c2[2]) ** 2
    )


def _find_color_name(r: int, g: int, b: int) -> str:
    """COLOR_DICTから最近傍色名を返す"""
    import sys
    sys.path.insert(0, '/home/arc_e/nanachi-color')
    try:
        from color_tool_handler import COLOR_DICT
    except ImportError:
        return "不明"

    best_name = "不明"
    best_dist = float("inf")
    for c in COLOR_DICT:
        hex_code = c["hex"].lstrip("#")
        try:
            cr = int(hex_code[0:2], 16)
            cg = int(hex_code[2:4], 16)
            cb = int(hex_code[4:6], 16)
        except ValueError:
            continue
        dist = _color_distance((r, g, b), (cr, cg, cb))
        if dist < best_dist:
            best_dist = dist
            best_name = c["name_jp"]
    return best_name


def extract_dominant_colors(image_bytes: bytes, n_colors: int = 5) -> List[Dict[str, Any]]:
    """画像バイト列から代表色をn_colors個抽出して返す

    Args:
        image_bytes: 画像のバイト列（JPEG/PNG等）
        n_colors: 抽出する代表色の数（デフォルト5）

    Returns:
        List of {
            "hex": "#RRGGBB",
            "rgb": {"r": int, "g": int, "b": int},
            "hsl": {"h": float, "s": float, "l": float},
            "name_jp": str,
            "ratio": float
        }

    Raises:
        ValueError: 画像の読み込みや処理に失敗した場合
    """
    n_colors = max(1, min(10, int(n_colors)))
    CLUSTER_THRESHOLD = 30  # ユークリッド距離の閾値

    # 1. PIL でRGBに変換
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert("RGB")
    except Exception as e:
        raise ValueError(f"画像の読み込みに失敗したぜ: {e}")

    # 2. 150x150にリサイズ（高速化）
    img = img.resize((150, 150), Image.LANCZOS)

    # 3. ピクセルをRGBタプルで取得してカウント
    pixels = list(img.getdata())
    total_pixels = len(pixels)

    if total_pixels == 0:
        raise ValueError("画像にピクセルデータがないぜ")

    # ピクセルカウント
    pixel_counts: Dict[tuple, int] = {}
    for px in pixels:
        # 量子化: 8段階に丸めて色数を減らす
        quantized = (
            (px[0] // 8) * 8,
            (px[1] // 8) * 8,
            (px[2] // 8) * 8,
        )
        pixel_counts[quantized] = pixel_counts.get(quantized, 0) + 1

    # 出現頻度でソート
    sorted_colors = sorted(pixel_counts.items(), key=lambda x: -x[1])

    # 4. 似た色をクラスタリング（ユークリッド距離でグループ化、閾値30）
    clusters: List[Dict[str, Any]] = []

    for color, count in sorted_colors:
        # 既存クラスターに近い色がないか探す
        merged = False
        for cluster in clusters:
            if _color_distance(color, cluster["center"]) < CLUSTER_THRESHOLD:
                cluster["count"] += count
                # 加重平均でセンターを更新
                total = cluster["count"]
                prev_w = (total - count) / total
                new_w = count / total
                cluster["center"] = (
                    cluster["center"][0] * prev_w + color[0] * new_w,
                    cluster["center"][1] * prev_w + color[1] * new_w,
                    cluster["center"][2] * prev_w + color[2] * new_w,
                )
                merged = True
                break

        if not merged:
            clusters.append({
                "center": (float(color[0]), float(color[1]), float(color[2])),
                "count": count,
            })

        # 十分なクラスター数になったら打ち切り（最大50クラスター程度で抑える）
        if len(clusters) >= 200:
            # クラスター数が多くなったら再マージ
            merged_clusters = []
            for cl in sorted(clusters, key=lambda x: -x["count"]):
                found = False
                for mc in merged_clusters:
                    if _color_distance(cl["center"], mc["center"]) < CLUSTER_THRESHOLD:
                        total = mc["count"] + cl["count"]
                        prev_w = mc["count"] / total
                        new_w = cl["count"] / total
                        mc["center"] = (
                            mc["center"][0] * prev_w + cl["center"][0] * new_w,
                            mc["center"][1] * prev_w + cl["center"][1] * new_w,
                            mc["center"][2] * prev_w + cl["center"][2] * new_w,
                        )
                        mc["count"] = total
                        found = True
                        break
                if not found:
                    merged_clusters.append(cl)
            clusters = merged_clusters

    # 出現頻度で再ソート
    clusters.sort(key=lambda x: -x["count"])

    # 上位n_colors個を取得
    top_clusters = clusters[:n_colors]
    top_total = sum(cl["count"] for cl in top_clusters)

    # 5. 各クラスターの平均色を計算して結果を生成
    result = []
    for cluster in top_clusters:
        r = int(round(cluster["center"][0]))
        g = int(round(cluster["center"][1]))
        b = int(round(cluster["center"][2]))

        # クランプ
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        # HEX文字列
        hex_code = "#{:02X}{:02X}{:02X}".format(r, g, b)

        # 6. 面積比率（ratio）を計算
        ratio = round(cluster["count"] / total_pixels, 4)

        # 7. color_tool_handler.py の COLOR_DICT と照合して近い色名を返す
        name_jp = _find_color_name(r, g, b)

        # HSL計算
        hsl = _rgb_to_hsl(r, g, b)

        result.append({
            "hex": hex_code,
            "rgb": {"r": r, "g": g, "b": b},
            "hsl": hsl,
            "name_jp": name_jp,
            "ratio": ratio,
        })

    return result
