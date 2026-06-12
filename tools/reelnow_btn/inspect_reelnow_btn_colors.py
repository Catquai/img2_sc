from __future__ import annotations

import colorsys
from collections import Counter
from pathlib import Path

from PIL import Image


SOURCE = Path(r"F:\工作\短视频\ReelNow\anime\btn")


def main() -> None:
    for name in ("notif_btn_l_25.png", "notif_btn_s_16.png"):
        path = SOURCE / name
        colors: Counter[tuple[int, int, int]] = Counter()
        with Image.open(path) as image:
            for red, green, blue, alpha in image.convert("RGBA").get_flattened_data():
                if alpha > 0:
                    colors[(red // 8 * 8, green // 8 * 8, blue // 8 * 8)] += 1
        print(name)
        for (red, green, blue), count in colors.most_common(12):
            hue, saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
            hls_hue, lightness, hls_saturation = colorsys.rgb_to_hls(
                red / 255, green / 255, blue / 255
            )
            print(
                (red, green, blue),
                count,
                f"hsv=({hue*360:.1f},{saturation:.2f},{value:.2f})",
                f"hsl=({hls_hue*360:.1f},{hls_saturation:.2f},{lightness:.2f})",
            )


if __name__ == "__main__":
    main()
