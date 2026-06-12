from __future__ import annotations

import colorsys
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageChops


SOURCE = Path(r"F:\工作\短视频\ReelNow\anime\btn")
OUTPUT_ROOT = Path(r"F:\img2-sc")


def natural_key(path: Path) -> tuple[str, int]:
    match = re.match(r"(.+)_0*(\d+)$", path.stem)
    return (match.group(1), int(match.group(2))) if match else (path.stem, 0)


def group_name(path: Path) -> str:
    if path.stem.startswith("notif_btn_l_"):
        return "notif_btn_l"
    if path.stem.startswith("notif_btn_s_"):
        return "notif_btn_s"
    return path.stem.rsplit("_", 1)[0]


def choose_target_hue(source_hue: float) -> float:
    candidates = [
        20 / 360, 110 / 360, 235 / 360, 262 / 360,
        286 / 360, 318 / 360, 342 / 360,
    ]
    far_candidates = [
        hue for hue in candidates
        if min(abs(hue - source_hue), 1 - abs(hue - source_hue)) >= (60 / 360)
    ]
    return random.choice(far_candidates or candidates)


TARGET_HUE = 0.0
TARGET_HUE_DEG = 0
OUTPUT = OUTPUT_ROOT


def recolor_pixel(pixel: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    red, green, blue, alpha = pixel
    if alpha == 0:
        return pixel

    hue, hsv_saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
    if hsv_saturation < 0.08:
        return pixel

    hls_hue, lightness, hsl_saturation = colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)

    # Low-saturation orange pixels are the moving shine. Use the current
    # hue-independent HSL shine rule: S=60%-75%, preserve lightness and alpha.
    if hsl_saturation < 0.58 or hsv_saturation < 0.42:
        target_hsl_saturation = min(0.75, max(0.60, hsl_saturation * 1.35))
        red_f, green_f, blue_f = colorsys.hls_to_rgb(
            TARGET_HUE, lightness, target_hsl_saturation
        )
        return round(red_f * 255), round(green_f * 255), round(blue_f * 255), alpha

    target_hsv_saturation = min(0.86, max(0.62, hsv_saturation * 1.10))
    red_f, green_f, blue_f = colorsys.hsv_to_rgb(TARGET_HUE, target_hsv_saturation, value)
    return round(red_f * 255), round(green_f * 255), round(blue_f * 255), alpha


def main() -> None:
    global TARGET_HUE, TARGET_HUE_DEG, OUTPUT
    files = sorted(SOURCE.glob("*.png"), key=natural_key)
    groups: dict[str, list[Path]] = defaultdict(list)
    for path in files:
        groups[group_name(path)].append(path)

    source_hues = []
    for path in files:
        with Image.open(path) as image:
            for red, green, blue, alpha in image.convert("RGBA").get_flattened_data():
                if alpha <= 0:
                    continue
                hue, saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
                if saturation >= 0.35 and value >= 0.35:
                    source_hues.append(hue)
    source_hue = sorted(source_hues)[len(source_hues) // 2]

    TARGET_HUE = choose_target_hue(source_hue)
    TARGET_HUE_DEG = round(TARGET_HUE * 360)
    OUTPUT = OUTPUT_ROOT / f"reelnow_btn_frame_output_h{TARGET_HUE_DEG:03d}"
    suffix = 2
    while OUTPUT.exists():
        OUTPUT = OUTPUT_ROOT / f"reelnow_btn_frame_output_h{TARGET_HUE_DEG:03d}_{suffix}"
        suffix += 1

    OUTPUT.mkdir(parents=True, exist_ok=False)
    dims: dict[str, Counter[tuple[int, int]]] = {}
    errors: list[str] = []
    changed = 0

    for path in files:
        out_path = OUTPUT / path.name
        with Image.open(path) as source_image:
            source = source_image.convert("RGBA")
            result = Image.new("RGBA", source.size)
            result.putdata([recolor_pixel(pixel) for pixel in source.get_flattened_data()])
            result.save(out_path)

        with Image.open(path) as source_image, Image.open(out_path) as output_image:
            source = source_image.convert("RGBA")
            output = output_image.convert("RGBA")
            if source.size != output.size:
                errors.append(f"size:{path.name}")
            if ImageChops.difference(source.getchannel("A"), output.getchannel("A")).getbbox():
                errors.append(f"alpha:{path.name}")
            if ImageChops.difference(source.convert("RGB"), output.convert("RGB")).getbbox():
                changed += 1

    for name, paths in sorted(groups.items()):
        counter: Counter[tuple[int, int]] = Counter()
        for path in paths:
            with Image.open(path) as image:
                counter[image.size] += 1
        dims[name] = counter

    print(f"source={SOURCE}")
    print(f"output={OUTPUT}")
    print(f"source_hue_deg={round(source_hue * 360)}")
    print(f"target_hue_deg={TARGET_HUE_DEG}")
    for name, paths in sorted(groups.items()):
        print(f"group={name} count={len(paths)} dims={dict(dims[name])}")
    print(
        f"processed={len(files)} changed={changed} "
        f"errors={len(errors)} names_preserved={len(list(OUTPUT.glob('*.png'))) == len(files)}"
    )
    if errors:
        print("\n".join(errors[:20]))


if __name__ == "__main__":
    main()
