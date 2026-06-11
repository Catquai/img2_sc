from __future__ import annotations

import re
from pathlib import Path

from PIL import Image


SOURCE = Path(r"F:\img2-sc\notification_frame_output_blue")
OUTPUT = Path(r"F:\img2-sc\notification_blue_all_frames.png")
FRAME_DURATION_MS = 50


def natural_key(path: Path) -> tuple[str, int]:
    match = re.match(r"(.+)_0*(\d+)$", path.stem)
    return (match.group(1), int(match.group(2))) if match else (path.stem, 0)


def main() -> None:
    paths = sorted(SOURCE.glob("*.png"), key=natural_key)
    images = [Image.open(path).convert("RGBA") for path in paths]
    width = max(image.width for image in images)
    height = max(image.height for image in images)

    frames = []
    for image in images:
        frame = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        x = (width - image.width) // 2
        y = (height - image.height) // 2
        frame.alpha_composite(image, (x, y))
        frames.append(frame)

    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        disposal=1,
        blend=0,
    )

    for image in images:
        image.close()

    with Image.open(OUTPUT) as result:
        print(
            f"output={OUTPUT} frames={result.n_frames} "
            f"canvas={result.width}x{result.height} duration_ms={FRAME_DURATION_MS}"
        )


if __name__ == "__main__":
    main()
