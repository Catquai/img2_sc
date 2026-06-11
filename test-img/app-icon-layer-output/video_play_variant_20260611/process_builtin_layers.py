from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
SIZE = 512


def crop_square_resize(path: Path, size: int = SIZE) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side)).resize((size, size), Image.Resampling.LANCZOS)


def remove_green_key(path: Path) -> Image.Image:
    img = crop_square_resize(path, SIZE)
    arr = np.array(img).astype(np.float32)
    rgb = arr[..., :3]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]

    green_dominance = g - np.maximum(r, b)
    green_distance = np.sqrt((r - 0) ** 2 + (g - 255) ** 2 + (b - 42) ** 2)
    key_score = np.maximum(green_dominance * 1.35, 255 - green_distance)
    alpha = np.clip((155 - key_score) * 3.1, 0, 255)

    subject_core = (g < 175) | (r > 80) | (b > 130)
    alpha = np.where(subject_core & (green_dominance < 85), np.maximum(alpha, 230), alpha)
    alpha = np.where((g > 180) & (green_dominance > 60), np.minimum(alpha, 45), alpha)

    # Despill visible edges.
    edge = (alpha > 0) & (alpha < 250)
    rgb[..., 1] = np.where(edge, np.minimum(g, (r + b) * 0.55), g)

    out = Image.fromarray(np.clip(np.dstack([rgb, alpha]), 0, 255).astype(np.uint8), "RGBA")
    return out


def scale_subject(img: Image.Image, percent: float = 0.70) -> Image.Image:
    bbox = img.getchannel("A").getbbox()
    if not bbox:
        return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    subject = img.crop(bbox)
    max_dim = int(SIZE * percent)
    scale = min(max_dim / subject.width, max_dim / subject.height)
    subject = subject.resize((max(1, int(subject.width * scale)), max(1, int(subject.height * scale))), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.alpha_composite(subject, ((SIZE - subject.width) // 2, (SIZE - subject.height) // 2))
    return out


def largest_component(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    best: list[tuple[int, int]] = []
    for sy in range(h):
        for sx in range(w):
            if not mask[sy, sx] or seen[sy, sx]:
                continue
            stack = [(sx, sy)]
            seen[sy, sx] = True
            comp: list[tuple[int, int]] = []
            while stack:
                x, y = stack.pop()
                comp.append((x, y))
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < w and 0 <= ny < h and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((nx, ny))
            if len(comp) > len(best):
                best = comp
    out = np.zeros_like(mask, dtype=np.uint8)
    for x, y in best:
        out[y, x] = 255
    return out


def play_button_hole_from_source(source_path: Path) -> Image.Image:
    src = crop_square_resize(source_path, SIZE).convert("RGB")
    # Tight center ROI around the visible rounded play button in the green-screen source.
    x0, y0, x1, y1 = 185, 178, 372, 360
    roi = np.asarray(src.crop((x0, y0, x1, y1)), dtype=np.int16)
    r, g, b = roi[..., 0], roi[..., 1], roi[..., 2]
    mx = np.maximum.reduce([r, g, b])
    mn = np.minimum.reduce([r, g, b])
    saturation = mx - mn
    brightness = (r + g + b) / 3
    not_green = ~((g > 150) & (g - np.maximum(r, b) > 45))
    # The play button is the only large bright saturated object in this ROI.
    raw = (brightness > 92) & (saturation > 38) & not_green & (r > 95) & (b > 80)
    comp = largest_component(raw)
    hole_roi = Image.fromarray(comp, "L")
    hole_roi = hole_roi.filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.MinFilter(7))
    hole_roi = hole_roi.filter(ImageFilter.GaussianBlur(1.0)).point(lambda p: 255 if p > 36 else 0)
    hole = Image.new("L", (SIZE, SIZE), 0)
    hole.paste(hole_roi, (x0, y0))
    hole.save(ROOT / "builtin_play_button_hole_mask_512.png")
    return hole


def white_negative_from_alpha(img: Image.Image, source_path: Path) -> Image.Image:
    alpha = img.getchannel("A")
    alpha = alpha.point(lambda p: 255 if p > 110 else 0)

    # Preserve the actual generated silhouette, but cut the center play icon
    # using the rounded triangle shape extracted from the green-screen source.
    hole = play_button_hole_from_source(source_path)
    alpha = Image.composite(Image.new("L", (SIZE, SIZE), 0), alpha, hole)

    white = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 255))
    white.putalpha(alpha)
    small = white.resize((72, 72), Image.Resampling.LANCZOS)
    small_alpha = small.getchannel("A").point(lambda p: 255 if p > 90 else 0)
    d = ImageDraw.Draw(small_alpha)
    d.rectangle((0, 0, 71, 0), fill=0)
    d.rectangle((0, 71, 71, 71), fill=0)
    d.rectangle((0, 0, 0, 71), fill=0)
    d.rectangle((71, 0, 71, 71), fill=0)
    small.putalpha(small_alpha)
    return small


def monochrome_icon_from_source(source_path: Path) -> tuple[Image.Image, Image.Image]:
    """Build a pure-white minimalist icon from the generated keyed source."""
    fg = remove_green_key(source_path)
    alpha = fg.getchannel("A")

    # Convert the generated foreground into a hard, single-color silhouette.
    solid = alpha.point(lambda p: 255 if p > 96 else 0)
    solid = solid.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))

    # Keep the generated film perforations and key-color cutouts as transparent
    # negative space, then carve the play button from the actual source image.
    play_hole = play_button_hole_from_source(source_path)
    solid = Image.composite(Image.new("L", (SIZE, SIZE), 0), solid, play_hole)

    # Remove accidental edge contact after simplification.
    edge = ImageDraw.Draw(solid)
    edge.rectangle((0, 0, SIZE - 1, 0), fill=0)
    edge.rectangle((0, SIZE - 1, SIZE - 1, SIZE - 1), fill=0)
    edge.rectangle((0, 0, 0, SIZE - 1), fill=0)
    edge.rectangle((SIZE - 1, 0, SIZE - 1, SIZE - 1), fill=0)

    mono_512 = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 255))
    mono_512.putalpha(solid)

    mono_72 = mono_512.resize((72, 72), Image.Resampling.LANCZOS)
    a72 = mono_72.getchannel("A").point(lambda p: 255 if p > 90 else 0)
    d72 = ImageDraw.Draw(a72)
    d72.rectangle((0, 0, 71, 0), fill=0)
    d72.rectangle((0, 71, 71, 71), fill=0)
    d72.rectangle((0, 0, 0, 71), fill=0)
    d72.rectangle((71, 0, 71, 71), fill=0)
    mono_72.putalpha(a72)
    return mono_512, mono_72


def checker(size: int = SIZE, cell: int = 16) -> Image.Image:
    img = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)
    for y in range(0, size, cell):
        for x in range(0, size, cell):
            if (x // cell + y // cell) % 2:
                d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(212, 218, 228, 255))
    return img


def save_checker(img: Image.Image, path: Path) -> None:
    base = checker()
    base.alpha_composite(img)
    base.save(path)


def save_dark_preview(img: Image.Image, path: Path) -> None:
    base = Image.new("RGBA", img.size, (18, 20, 32, 255))
    base.alpha_composite(img)
    base.save(path)


def contact_sheet(items: list[tuple[str, Path]], out: Path) -> None:
    cells = []
    for label, path in items:
        im = Image.open(path).convert("RGBA")
        im.thumbnail((160, 160), Image.Resampling.LANCZOS)
        cell = Image.new("RGBA", (190, 198), (245, 247, 250, 255))
        cell.alpha_composite(im, ((190 - im.width) // 2, 8))
        ImageDraw.Draw(cell).text((10, 176), label, fill=(25, 30, 42, 255), font=ImageFont.load_default())
        cells.append(cell)
    sheet = Image.new("RGBA", (190 * len(cells), 198), (232, 236, 242, 255))
    for i, cell in enumerate(cells):
        sheet.alpha_composite(cell, (i * 190, 0))
    sheet.save(out)


def main() -> None:
    fg_full = remove_green_key(ROOT / "builtin_foreground_keyed_source.png")
    bg = crop_square_resize(ROOT / "builtin_background_source.png", SIZE).convert("RGB")
    fg_70 = scale_subject(fg_full)
    negative = white_negative_from_alpha(fg_full, ROOT / "builtin_foreground_keyed_source.png")
    mono_512, mono_72 = monochrome_icon_from_source(ROOT / "builtin_foreground_keyed_source.png")

    fg_full.save(ROOT / "builtin_foreground_alpha_full_512.png")
    fg_70.save(ROOT / "builtin_foreground_70pct_512.png")
    bg.save(ROOT / "builtin_background_512.png")
    negative.save(ROOT / "builtin_white_negative_72.png")
    mono_512.save(ROOT / "builtin_mono_icon_512.png")
    mono_72.save(ROOT / "builtin_mono_icon_72.png")
    save_dark_preview(mono_512, ROOT / "builtin_mono_icon_512_dark_preview.png")
    save_dark_preview(mono_72.resize((512, 512), Image.Resampling.NEAREST), ROOT / "builtin_mono_icon_72_dark_preview.png")
    save_checker(fg_full, ROOT / "builtin_foreground_alpha_full_checker.png")
    save_checker(fg_70, ROOT / "builtin_foreground_70pct_checker.png")

    comp = bg.convert("RGBA")
    comp.alpha_composite(fg_full)
    comp.save(ROOT / "builtin_composite_full_subject_preview.png")

    contact_sheet(
        [
            ("foreground 70%", ROOT / "builtin_foreground_70pct_512.png"),
            ("background", ROOT / "builtin_background_512.png"),
            ("negative 72", ROOT / "builtin_white_negative_72.png"),
            ("mono 72", ROOT / "builtin_mono_icon_72.png"),
            ("full preview", ROOT / "builtin_composite_full_subject_preview.png"),
        ],
        ROOT / "builtin_contact_sheet.png",
    )


if __name__ == "__main__":
    main()
