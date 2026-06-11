from __future__ import annotations

import colorsys
import re
from pathlib import Path

from PIL import Image, ImageChops


SOURCE = Path(r"F:\工作\五组\算号器\新建文件夹\notification")
OUTPUT = Path(r"F:\img2-sc\notification_frame_output_blue")
TARGET_HUE = 216.0 / 360.0


def natural_key(path: Path) -> tuple[str, int]:
    match = re.match(r"(.+)_0*(\d+)$", path.stem)
    return (match.group(1), int(match.group(2))) if match else (path.stem, 0)


def recolor_pixel(pixel: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    red, green, blue, alpha = pixel
    hue, saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)

    # Keep neutral shine/highlight pixels neutral. Recolor only the gold/orange body.
    if saturation >= 0.12 and 0.03 <= hue <= 0.18:
        saturation = min(1.0, saturation * 1.15)
        red_f, green_f, blue_f = colorsys.hsv_to_rgb(TARGET_HUE, saturation, value)
        return round(red_f * 255), round(green_f * 255), round(blue_f * 255), alpha

    return red, green, blue, alpha


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    files = sorted(SOURCE.glob("*.png"), key=natural_key)

    for source_path in files:
        with Image.open(source_path) as source_image:
            rgba = source_image.convert("RGBA")
            result = Image.new("RGBA", rgba.size)
            result.putdata([recolor_pixel(pixel) for pixel in rgba.get_flattened_data()])
            result.save(OUTPUT / source_path.name, format="PNG")

    errors = []
    changed = 0
    output_files = sorted(OUTPUT.glob("*.png"), key=natural_key)
    for source_path, output_path in zip(files, output_files):
        with Image.open(source_path) as source_image, Image.open(output_path) as output_image:
            source_rgba = source_image.convert("RGBA")
            output_rgba = output_image.convert("RGBA")
            if source_rgba.size != output_rgba.size:
                errors.append(f"size:{source_path.name}")
            if ImageChops.difference(
                source_rgba.getchannel("A"), output_rgba.getchannel("A")
            ).getbbox():
                errors.append(f"alpha:{source_path.name}")
            if ImageChops.difference(source_rgba.convert("RGB"), output_rgba.convert("RGB")).getbbox():
                changed += 1

    names_equal = [path.name for path in files] == [path.name for path in output_files]
    print(
        f"processed={len(files)} output_count={len(output_files)} "
        f"names_equal={names_equal} changed={changed} errors={len(errors)} output={OUTPUT}"
    )


if __name__ == "__main__":
    main()
