from __future__ import annotations

import colorsys
import re
from pathlib import Path

from PIL import Image, ImageSequence


OUTPUT = Path(r"F:\img2-sc\notification_blue_all_frames.png")


def natural_key(path: Path) -> tuple[str, int]:
    match = re.match(r"(.+)_0*(\d+)$", path.stem)
    return (match.group(1), int(match.group(2))) if match else (path.stem, 0)


def luminance(pixel: tuple[int, int, int, int]) -> float:
    red, green, blue, _ = pixel
    return (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255


def main() -> None:
    with Image.open(OUTPUT) as animation:
        frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(animation)]

    for group_index, group in enumerate(("an1", "an2", "an3")):
        group_frames = frames[group_index * 60 : (group_index + 1) * 60]
        base = group_frames[0]
        base_pixels = list(base.get_flattened_data())
        print(group, f"frames={len(group_frames)} size={base.size}")
        for index in (15, 30, 45):
            frame = group_frames[index]
            shine_luminance = []
            base_luminance = []
            shine_saturation = []
            for base_pixel, frame_pixel in zip(base_pixels, frame.get_flattened_data()):
                difference = sum(abs(a - b) for a, b in zip(base_pixel[:3], frame_pixel[:3]))
                if difference > 18 and frame_pixel[3] > 0:
                    shine_luminance.append(luminance(frame_pixel))
                    base_luminance.append(luminance(base_pixel))
                    _, saturation, _ = colorsys.rgb_to_hsv(
                        frame_pixel[0] / 255, frame_pixel[1] / 255, frame_pixel[2] / 255
                    )
                    shine_saturation.append(saturation)

            delta = sum(
                shine - base_value
                for shine, base_value in zip(shine_luminance, base_luminance)
            ) / len(shine_luminance)
            print(
                f"{group}_{index:03}.png",
                f"shine_pixels={len(shine_luminance)}",
                f"shine_lum={sum(shine_luminance) / len(shine_luminance):.3f}",
                f"base_lum={sum(base_luminance) / len(base_luminance):.3f}",
                f"delta={delta:.3f}",
                f"shine_sat={sum(shine_saturation) / len(shine_saturation):.3f}",
            )


if __name__ == "__main__":
    main()
