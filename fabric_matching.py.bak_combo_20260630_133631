"""
布生地在庫から配色マッチングを行うモジュール
"""
import json, sys
sys.path.insert(0, '/home/arc_e/nanachi-color')
sys.path.insert(0, '/home/arc_e')


def match_fabrics_from_inventory(uploaded_colors: list, harmony_type: str = "all") -> str:
    """
    アップロードされた布の色から、在庫の布生地との配色マッチングを実行

    Args:
        uploaded_colors: [{"hex":"#RRGGBB","name_jp":"色名",...}, ...]
        harmony_type: "complementary"|"analogous"|"all"

    Returns:
        整形済みテキスト（LLMへの回答用）
    """
    try:
        from fabric_inventory import FabricInventory
        inv = FabricInventory()
        all_fabric_colors = inv.get_all_colors()
    except ImportError:
        return "布生地在庫モジュール（fabric_inventory）がまだ準備中だぜ。Task Bの完成を待ってくれな。"
    except Exception as e:
        return f"在庫取得中にエラーが発生したぜ: {e}"

    try:
        from color_tool_handler import color_harmonize
    except ImportError:
        color_harmonize = None

    if not all_fabric_colors:
        return "在庫に布生地がまだ登録されていないぜ。写真を撮って登録してくれ。"

    results = []
    for uc in uploaded_colors[:3]:  # 最大3色を基準に
        base_hex = uc.get("hex", "")
        if not base_hex:
            continue

        # 在庫の各布生地色との距離を計算
        matches = []
        for fc in all_fabric_colors:
            fc_hex = fc.get("hex", "")
            if not fc_hex:
                continue
            dist = _hex_distance(base_hex, fc_hex)
            matches.append({**fc, "distance": dist, "base_color": uc.get("name_jp", "?")})

        # 距離でソート
        matches.sort(key=lambda x: x["distance"])

        # 配色理論でも参照用に計算
        harmonic_hexes = set()
        if color_harmonize:
            try:
                harmonic_mode = harmony_type if harmony_type != "all" else "analogous"
                harmonic = color_harmonize(base_hex, harmonic_mode)
                harmonic_hexes = {h["hex"] for h in harmonic}
            except Exception:
                pass

        results.append({
            "base": uc,
            "close_matches": matches[:3],
            "harmonic_refs": harmonic_hexes
        })

    return _format_matching_result(results, all_fabric_colors)


def _hex_distance(hex1: str, hex2: str) -> float:
    """2つのHEXコードのRGB空間距離"""
    def parse(h):
        h = h.lstrip('#')
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r1, g1, b1 = parse(hex1)
    r2, g2, b2 = parse(hex2)
    return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5


def _format_matching_result(results: list, all_colors: list) -> str:
    """マッチング結果を読みやすいテキストに整形"""
    lines = ["【在庫布生地との配色マッチング結果】\n"]
    for r in results:
        base = r["base"]
        lines.append(f"■ 基準色: {base.get('name_jp', '?')}（{base.get('hex', '')}）")
        lines.append("  近い色の在庫布生地:")
        for m in r["close_matches"]:
            lines.append(
                f"    → 「{m.get('fabric_name', '?')}」の{m.get('name_jp', '?')}（{m.get('hex', '')}）距離:{m['distance']:.0f}"
            )
        lines.append("")
    return "\n".join(lines)
