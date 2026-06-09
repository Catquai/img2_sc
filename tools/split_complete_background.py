from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image, ImageFilter


def parse_hex_color(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    return tuple(int(text[index:index + 2], 16) for index in (0, 2, 4))


def is_key_like(pixel: tuple[int, int, int, int], key: tuple[int, int, int]) -> bool:
    r, g, b, a = pixel
    if a == 0:
        return True
    kr, kg, kb = key
    distance = ((r - kr) ** 2 + (g - kg) ** 2 + (b - kb) ** 2) ** 0.5
    magenta_like = r >= 175 and b >= 145 and g <= 135 and min(r, b) - g >= 45
    return distance <= 155 and magenta_like


def connected_key_background(image: Image.Image, key: tuple[int, int, int]) -> list[list[bool]]:
    width, height = image.size
    pixels = image.load()
    visited = [[False for _ in range(width)] for _ in range(height)]
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if x < 0 or y < 0 or x >= width or y >= height or visited[y][x]:
            continue
        if not is_key_like(pixels[x, y], key):
            continue
        visited[y][x] = True
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return visited


def largest_component_mask(mask: list[list[bool]]) -> Image.Image:
    height = len(mask)
    width = len(mask[0])
    seen = [[False for _ in range(width)] for _ in range(height)]
    best: list[tuple[int, int]] = []

    for sy in range(height):
        for sx in range(width):
            if seen[sy][sx] or not mask[sy][sx]:
                continue
            comp: list[tuple[int, int]] = []
            queue = deque([(sx, sy)])
            seen[sy][sx] = True
            while queue:
                x, y = queue.popleft()
                comp.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < width and 0 <= ny < height and not seen[ny][nx] and mask[ny][nx]:
                        seen[ny][nx] = True
                        queue.append((nx, ny))
            if len(comp) > len(best):
                best = comp

    out = Image.new("L", (width, height), 0)
    pixels = out.load()
    for x, y in best:
        pixels[x, y] = 255
    return out


def build_subject_mask(keyed_foreground: Path, key: tuple[int, int, int], dilate: int) -> Image.Image:
    keyed = Image.open(keyed_foreground).convert("RGBA")
    bg = connected_key_background(keyed, key)
    subject = [[not bg[y][x] for x in range(keyed.width)] for y in range(keyed.height)]
    mask = largest_component_mask(subject)
    if dilate > 0:
        mask = mask.filter(ImageFilter.MaxFilter(dilate * 2 + 1))
    return mask


def inpaint_diffusion(source: Image.Image, mask: Image.Image, downscale: int, passes: int) -> Image.Image:
    width, height = source.size
    small_size = (max(1, width // downscale), max(1, height // downscale))
    small = source.resize(small_size, Image.Resampling.LANCZOS).convert("RGB")
    small_mask = mask.resize(small_size, Image.Resampling.NEAREST).convert("L")

    pix = small.load()
    mpix = small_mask.load()
    known = [[mpix[x, y] < 8 for x in range(small.width)] for y in range(small.height)]

    for _ in range(passes):
        updates: list[tuple[int, int, tuple[int, int, int]]] = []
        for y in range(small.height):
            for x in range(small.width):
                if known[y][x]:
                    continue
                vals = []
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1), (x + 1, y + 1), (x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1)):
                    if 0 <= nx < small.width and 0 <= ny < small.height and known[ny][nx]:
                        vals.append(pix[nx, ny])
                if vals:
                    r = round(sum(v[0] for v in vals) / len(vals))
                    g = round(sum(v[1] for v in vals) / len(vals))
                    b = round(sum(v[2] for v in vals) / len(vals))
                    updates.append((x, y, (r, g, b)))
        if not updates:
            break
        for x, y, color in updates:
            pix[x, y] = color
            known[y][x] = True

    # Smooth filled area at low resolution, then upsample. Original unmasked pixels
    # are restored afterward, so blur affects only the reconstructed hole.
    small = small.filter(ImageFilter.GaussianBlur(3))
    filled = small.resize((width, height), Image.Resampling.BICUBIC).convert("RGBA")
    original = source.convert("RGBA")
    result = Image.composite(filled, original, mask)
    return result.convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--composite", required=True, type=Path)
    parser.add_argument("--keyed-foreground", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mask-output", required=True, type=Path)
    parser.add_argument("--key", default="#ff00ff")
    parser.add_argument("--dilate", type=int, default=18)
    parser.add_argument("--downscale", type=int, default=6)
    parser.add_argument("--passes", type=int, default=260)
    args = parser.parse_args()

    key = parse_hex_color(args.key)
    composite = Image.open(args.composite).convert("RGBA")
    mask = build_subject_mask(args.keyed_foreground, key, args.dilate)
    background = inpaint_diffusion(composite, mask, args.downscale, args.passes)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    background.save(args.output)
    mask.save(args.mask_output)


if __name__ == "__main__":
    main()
