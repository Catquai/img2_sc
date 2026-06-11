from __future__ import annotations

import colorsys
from pathlib import Path

from PIL import Image, ImageChops, ImageSequence


SOURCE = Path(r"F:\img2-sc\notification_blue_all_frames.png")
OUTPUT = Path(r"F:\img2-sc\notification_blue_all_frames_saturated_shine.png")
FRAME_DURATION_MS = 50


def enhance_pixel(pixel: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    red, green, blue, alpha = pixel
    if alpha == 0:
        return pixel

    hue, saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)

    # The static body is strongly saturated. Raise only the pale blue shine layer.
    if 0.54 <= hue <= 0.68 and 0.08 <= saturation < 0.68 and value > 0.50:
        target_saturation = min(0.68, max(saturation * 1.40, saturation + 0.10))
        red_f, green_f, blue_f = colorsys.hsv_to_rgb(hue, target_saturation, value)
        return round(red_f * 255), round(green_f * 255), round(blue_f * 255), alpha

    return pixel


def main() -> None:
    with Image.open(SOURCE) as animation:
        frames = []
        durations = []
        for frame in ImageSequence.Iterator(animation):
            rgba = frame.convert("RGBA")
            result = Image.new("RGBA", rgba.size)
            result.putdata([enhance_pixel(pixel) for pixel in rgba.get_flattened_data()])
            frames.append(result)
            durations.append(frame.info.get("duration", FRAME_DURATION_MS))

    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        disposal=1,
        blend=0,
    )

    with Image.open(OUTPUT) as result:
        print(f"output={OUTPUT} frames={result.n_frames} canvas={result.size}")

    with Image.open(SOURCE) as before_animation, Image.open(OUTPUT) as after_animation:
        before_frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(before_animation)]
        after_frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(after_animation)]
        changed_frames = 0
        alpha_errors = 0
        for before, after in zip(before_frames, after_frames):
            if ImageChops.difference(before.convert("RGB"), after.convert("RGB")).getbbox():
                changed_frames += 1
            if ImageChops.difference(before.getchannel("A"), after.getchannel("A")).getbbox():
                alpha_errors += 1
        print(f"changed_frames={changed_frames} alpha_errors={alpha_errors}")

        preview_indices = (15, 30, 75, 90, 135, 150)
        preview = Image.new("RGB", (964 * 2, 180 * len(preview_indices)), (35, 35, 35))
        for row, index in enumerate(preview_indices):
            background_before = Image.new("RGBA", before_frames[index].size, (238, 241, 247, 255))
            background_after = background_before.copy()
            background_before.alpha_composite(before_frames[index])
            background_after.alpha_composite(after_frames[index])
            preview.paste(background_before.convert("RGB"), (0, row * 180))
            preview.paste(background_after.convert("RGB"), (964, row * 180))
        preview.save(OUTPUT.with_name("notification_shine_before_after.png"))


if __name__ == "__main__":
    main()
