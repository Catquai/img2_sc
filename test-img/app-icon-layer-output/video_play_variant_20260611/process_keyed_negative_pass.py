from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parent
SIZE = 512
KEY = (0, 255, 42, 255)
WHITE = (255, 255, 255, 255)


def crop_square_resize(path: Path, size: int = SIZE) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side)).resize((size, size), Image.Resampling.LANCZOS)


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
    x0, y0, x1, y1 = 185, 178, 372, 360
    roi = np.asarray(src.crop((x0, y0, x1, y1)), dtype=np.int16)
    r, g, b = roi[..., 0], roi[..., 1], roi[..., 2]
    mx = np.maximum.reduce([r, g, b])
    mn = np.minimum.reduce([r, g, b])
    saturation = mx - mn
    brightness = (r + g + b) / 3
    not_green = ~((g > 150) & (g - np.maximum(r, b) > 45))
    raw = (brightness > 92) & (saturation > 38) & not_green & (r > 95) & (b > 80)
    comp = largest_component(raw)
    hole_roi = Image.fromarray(comp, "L")
    hole_roi = hole_roi.filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.MinFilter(7))
    hole_roi = hole_roi.filter(ImageFilter.GaussianBlur(1.0)).point(lambda p: 255 if p > 36 else 0)
    hole = Image.new("L", (SIZE, SIZE), 0)
    hole.paste(hole_roi, (x0, y0))
    hole.save(ROOT / "keyed_negative_play_hole_mask_512.png")
    return hole


def normalize_keyed_negative(raw_path: Path, foreground_source_path: Path) -> Image.Image:
    raw = crop_square_resize(raw_path, SIZE).convert("RGB")
    arr = np.asarray(raw, dtype=np.int16)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    green_like = (g > 105) & (g - np.maximum(r, b) > 18)

    # The image-generation pass may leave antialiasing or slight off-white;
    # normalize to exactly two colors: white subject and key background.
    out = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
    out[:, :] = KEY
    out[~green_like] = WHITE
    keyed = Image.fromarray(out, "RGBA")

    # The play cutout must be readable. If the generated keyed negative keeps
    # the whole center screen as key color, the play hole disappears into it;
    # fill a simple white screen plate first, then cut the real rounded play
    # button shape out of that plate.
    draw = ImageDraw.Draw(keyed)
    draw.rounded_rectangle((135, 176, 378, 370), radius=22, fill=WHITE)

    hole = play_button_hole_from_source(foreground_source_path)
    key_layer = Image.new("RGBA", (SIZE, SIZE), KEY)
    keyed = Image.composite(key_layer, keyed, hole)
    keyed.save(ROOT / "builtin_negative_keyed_source_normalized.png")
    return keyed


def remove_key_to_alpha(keyed: Image.Image) -> Image.Image:
    arr = np.asarray(keyed.convert("RGBA"), dtype=np.uint8)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    is_key = (g > 180) & (g - np.maximum(r, b) > 80)
    out = np.zeros_like(arr)
    out[..., :3] = 255
    out[..., 3] = np.where(is_key, 0, 255).astype(np.uint8)
    alpha = Image.fromarray(out, "RGBA")
    alpha.save(ROOT / "builtin_negative_alpha_original.png")
    return alpha


def resize_whole_canvas_to_72(alpha: Image.Image) -> Image.Image:
    small = alpha.resize((72, 72), Image.Resampling.LANCZOS)
    a = small.getchannel("A").point(lambda p: 255 if p > 90 else 0)
    d = ImageDraw.Draw(a)
    d.rectangle((0, 0, 71, 0), fill=0)
    d.rectangle((0, 71, 71, 71), fill=0)
    d.rectangle((0, 0, 0, 71), fill=0)
    d.rectangle((71, 0, 71, 71), fill=0)
    final = Image.new("RGBA", (72, 72), WHITE)
    final.putalpha(a)
    final.save(ROOT / "builtin_negative_from_keyed_72.png")
    return final


def save_dark_preview(img: Image.Image, path: Path, scale: int = 1) -> None:
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale), Image.Resampling.NEAREST)
    bg = Image.new("RGBA", img.size, (18, 20, 32, 255))
    bg.alpha_composite(img)
    bg.save(path)


def main() -> None:
    keyed = normalize_keyed_negative(
        ROOT / "builtin_negative_keyed_generated_raw.png",
        ROOT / "builtin_foreground_keyed_source.png",
    )
    alpha = remove_key_to_alpha(keyed)
    final = resize_whole_canvas_to_72(alpha)
    save_dark_preview(alpha, ROOT / "builtin_negative_alpha_original_dark_preview.png")
    save_dark_preview(final, ROOT / "builtin_negative_from_keyed_72_dark_preview.png", scale=8)


if __name__ == "__main__":
    main()
