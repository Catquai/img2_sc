from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image


def parse_hex_color(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) != 6:
        raise ValueError("Key color must be #rrggbb")
    return tuple(int(text[index:index + 2], 16) for index in (0, 2, 4))


def is_key_like(pixel: tuple[int, int, int, int], key: tuple[int, int, int]) -> bool:
    r, g, b, a = pixel
    if a == 0:
        return True
    kr, kg, kb = key
    distance = ((r - kr) ** 2 + (g - kg) ** 2 + (b - kb) ** 2) ** 0.5
    magenta_like = r >= 130 and b >= 130 and g <= 115 and min(r, b) - g >= 45
    return distance <= 185 and magenta_like


def connected_background(image: Image.Image, key: tuple[int, int, int]) -> list[list[bool]]:
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
        queue.append((x + 1, y))
        queue.append((x - 1, y))
        queue.append((x, y + 1))
        queue.append((x, y - 1))

    return visited


def clean_spill(r: int, g: int, b: int) -> tuple[int, int, int]:
    magenta_excess = min(r, b) - g
    if magenta_excess > 18 and r > 185 and b > 150:
        r = max(g + 12, int(r - magenta_excess * 0.85))
        b = max(g + 12, int(b - magenta_excess * 0.35))
    return max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))


def process(
    source: Path,
    output: Path,
    key: tuple[int, int, int],
    preserve_disconnected_key_like: bool,
    alpha_input: bool,
) -> None:
    image = Image.open(source).convert("RGBA")
    pixels = image.load()

    if alpha_input:
        for y in range(image.height):
            for x in range(image.width):
                if is_key_like(pixels[x, y], key):
                    pixels[x, y] = (0, 0, 0, 0)
        output.parent.mkdir(parents=True, exist_ok=True)
        image.save(output)
        return

    bg = connected_background(image, key)
    for y in range(image.height):
        for x in range(image.width):
            # Key-like pixels are background by default, even when trapped between
            # separate foreground elements. If the subject needs real magenta or
            # purple material, choose a different key color and declare it in JSON.
            key_like = is_key_like(pixels[x, y], key)
            if bg[y][x] or (key_like and not preserve_disconnected_key_like):
                pixels[x, y] = (0, 0, 0, 0)
            else:
                r, g, b, a = pixels[x, y]
                r, g, b = clean_spill(r, g, b)
                pixels[x, y] = (r, g, b, max(a, 255))

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def checker_preview(source: Path, output: Path, tile: int = 16) -> None:
    image = Image.open(source).convert("RGBA")
    checker = Image.new("RGBA", image.size, (0, 0, 0, 255))
    pixels = checker.load()
    for y in range(image.height):
        for x in range(image.width):
            shade = 176 if ((x // tile) + (y // tile)) % 2 == 0 else 128
            pixels[x, y] = (shade, shade, shade, 255)
    checker.alpha_composite(image)
    output.parent.mkdir(parents=True, exist_ok=True)
    checker.save(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    parser.add_argument("--key", default="#ff00ff")
    parser.add_argument(
        "--preserve-disconnected-key-like",
        action="store_true",
        help="Keep disconnected key-like pixels only when JSON declares them as subject material.",
    )
    parser.add_argument(
        "--alpha-input",
        action="store_true",
        help="Treat source as an existing transparent PNG and only purge visible key-like pixels while preserving other alpha.",
    )
    args = parser.parse_args()

    process(args.source, args.output, parse_hex_color(args.key), args.preserve_disconnected_key_like, args.alpha_input)
    checker_preview(args.output, args.preview)


if __name__ == "__main__":
    main()
