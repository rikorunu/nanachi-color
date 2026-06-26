#!/usr/bin/env python3
"""ナナチカラー color_tool_handler テスト"""
import sys
sys.path.insert(0, '/home/arc_e/nanachi-color')
sys.path.insert(0, '/home/arc_e')

def test_all():
    try:
        from color_tool_handler import (
            color_hex_info, color_harmonize, color_random_palette,
            color_contrast_check, color_name_search, color_blend
        )
        print("✅ import OK")
    except ImportError as e:
        print(f"⚠️ import error (Task B未完成の可能性): {e}")
        return

    # test 1: color_hex_info
    info = color_hex_info("#FF5733")
    assert "rgb" in info, "color_hex_info: rgb keyがない"
    assert "name_jp" in info, "color_hex_info: name_jp keyがない"
    print(f"✅ color_hex_info: {info['name_jp']}({info['hex']})")

    # test 2: color_harmonize
    palette = color_harmonize("#3498DB", "complementary")
    assert len(palette) >= 2, "color_harmonize: 2色以上返ってこない"
    print(f"✅ color_harmonize complementary: {[c['hex'] for c in palette]}")

    # test 3: color_random_palette
    rand = color_random_palette(count=5)
    assert len(rand) == 5, f"color_random_palette: 5色じゃない ({len(rand)}色)"
    print(f"✅ color_random_palette: {[c['hex'] for c in rand]}")

    # test 4: color_contrast_check
    result = color_contrast_check("#FFFFFF", "#000000")
    assert result["contrast_ratio"] >= 21, "白黒コントラスト比が21未満"
    assert result["wcag_aaa"] == True, "白黒でWCAG AAAが通っていない"
    print(f"✅ color_contrast_check: ratio={result['contrast_ratio']:.1f} AAA={result['wcag_aaa']}")

    # test 5: color_name_search
    found = color_name_search("桜")
    assert len(found) >= 1, "color_name_search: 桜色が見つからない"
    print(f"✅ color_name_search 桜: {found[0]['name_jp']} {found[0]['hex']}")

    # test 6: color_blend
    gradient = color_blend("#FF0000", "#0000FF", steps=5)
    assert len(gradient) == 5, f"color_blend: 5色じゃない ({len(gradient)}色)"
    print(f"✅ color_blend: {[c['hex'] for c in gradient]}")

    print("\n🎨 全テスト通過だぜ！")

if __name__ == "__main__":
    test_all()
