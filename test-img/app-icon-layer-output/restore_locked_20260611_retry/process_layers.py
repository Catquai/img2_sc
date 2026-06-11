from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
SIZE = 1254
KEY = np.array([0, 255, 42], dtype=np.float32)


def remove_key(src_path: Path, out_path: Path) -> Image.Image:
    img = Image.open(src_path).convert("RGBA")
    arr = np.asarray(img, dtype=np.float32)
    rgb = arr[..., :3]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    dist = np.linalg.norm(rgb - KEY, axis=2)
    green_dom = g - np.maximum(r, b)

    # Smooth alpha ramp, tuned for the generated #00ff2a key background.
    alpha = np.clip((dist - 22) * 5.0, 0, 255)
    alpha = np.where((g > 165) & (green_dom > 45), np.minimum(alpha, 30), alpha)
    alpha = np.where((g > 210) & (green_dom > 90), 0, alpha)

    edge = (alpha > 0) & (alpha < 255)
    rgb[..., 1] = np.where(edge, np.minimum(g, (r + b) * 0.55), g)
    out = np.dstack([rgb, alpha]).clip(0, 255).astype(np.uint8)
    result = Image.fromarray(out, "RGBA")
    result.save(out_path)
    return result


def compose(foreground: Image.Image, background_path: Path, out_path: Path) -> Image.Image:
    bg = Image.open(background_path).convert("RGBA")
    if bg.size != foreground.size:
        bg = bg.resize(foreground.size, Image.Resampling.LANCZOS)
    bg.alpha_composite(foreground)
    bg.save(out_path)
    return bg


def contact_sheet(items: list[tuple[str, Path]], out_path: Path) -> None:
    cells = []
    for label, path in items:
        im = Image.open(path).convert("RGBA")
        im.thumbnail((220, 220), Image.Resampling.LANCZOS)
        cell = Image.new("RGBA", (250, 252), (245, 247, 250, 255))
        cell.alpha_composite(im, ((250 - im.width) // 2, 8))
        ImageDraw.Draw(cell).text((10, 228), label, fill=(24, 28, 38, 255), font=ImageFont.load_default())
        cells.append(cell)
    sheet = Image.new("RGBA", (250 * len(cells), 252), (232, 236, 242, 255))
    for i, cell in enumerate(cells):
        sheet.alpha_composite(cell, (i * 250, 0))
    sheet.save(out_path)


def main() -> None:
    fg = remove_key(ROOT / "foreground_keyed_source.png", ROOT / "foreground_alpha_1254.png")
    compose(fg, ROOT / "background_1254.png", ROOT / "composite_check_1254.png")
    contact_sheet(
        [
            ("reference", ROOT / "reference.png"),
            ("foreground keyed", ROOT / "foreground_keyed_source.png"),
            ("foreground alpha", ROOT / "foreground_alpha_1254.png"),
            ("background", ROOT / "background_1254.png"),
            ("composite check", ROOT / "composite_check_1254.png"),
        ],
        ROOT / "contact_sheet.png",
    )


if __name__ == "__main__":
    main()
