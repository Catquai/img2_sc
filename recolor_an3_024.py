from __future__ import annotations

import colorsys
from pathlib import Path

from PIL import Image, ImageChops


SOURCE = Path(r"F:\工作\五组\算号器\Pure Loan Calculator\notification\an3_024.png")
OUTPUT = Path(r"F:\img2-sc\an3_024_blue_saturated_shine.png")
TARGET_HUE = 216 / 360


def recolor(pixel: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    red, green, blue, alpha = pixel
    if alpha == 0:
        return pixel

    hue, saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
    if not 0.03 <= hue <= 0.18:
        return pixel

    # Lower-saturation pixels belong to the moving shine. Keep HSL saturation
    # in the hue-independent 60%-75% range to avoid a gray/muddy appearance.
    if saturation < 0.55:
        hls_hue, lightness, hls_saturation = colorsys.rgb_to_hls(
            red / 255, green / 255, blue / 255
        )
        target_hls_saturation = min(0.75, max(0.60, hls_saturation * 1.35))
        red_f, green_f, blue_f = colorsys.hls_to_rgb(
            TARGET_HUE, lightness, target_hls_saturation
        )
        return round(red_f * 255), round(green_f * 255), round(blue_f * 255), alpha
    else:
        target_saturation = min(0.78, saturation * 1.08)

    red_f, green_f, blue_f = colorsys.hsv_to_rgb(TARGET_HUE, target_saturation, value)
    return round(red_f * 255), round(green_f * 255), round(blue_f * 255), alpha


def main() -> None:
    with Image.open(SOURCE) as source_image:
        source = source_image.convert("RGBA")
        output = Image.new("RGBA", source.size)
        output.putdata([recolor(pixel) for pixel in source.get_flattened_data()])
        output.save(OUTPUT)

    with Image.open(SOURCE) as source_image, Image.open(OUTPUT) as output_image:
        source = source_image.convert("RGBA")
        output = output_image.convert("RGBA")
        alpha_equal = not ImageChops.difference(
            source.getchannel("A"), output.getchannel("A")
        ).getbbox()
        print(f"output={OUTPUT} size={output.size} alpha_equal={alpha_equal}")


if __name__ == "__main__":
    main()
