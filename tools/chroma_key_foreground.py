from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def clamp(value: float, low: int = 0, high: int = 255) -> int:
    return max(low, min(high, int(round(value))))


def parse_hex_color(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) != 6:
        raise ValueError("Key color must be #rrggbb")
    return tuple(int(text[index:index + 2], 16) for index in (0, 2, 4))


def remove_key(source: Path, output: Path, key: tuple[int, int, int]) -> None:
    image = Image.open(source).convert("RGBA")
    background = connected_key_background(image, key)
    pixels = image.load()
    kr, kg, kb = key

    for y in range(image.height):
        for x in range(image.width):
            if background[y][x]:
                pixels[x, y] = (0, 0, 0, 0)
                continue

            r, g, b, a = pixels[x, y]
            base_alpha = a / 255.0
            if base_alpha <= 0:
                pixels[x, y] = (0, 0, 0, 0)
                continue

            max_diff = max(abs(r - kr), abs(g - kg), abs(b - kb))
            alpha = max(0.0, min(1.0, (max_diff - 3.0) / 252.0)) * base_alpha

            if alpha < 0.01:
                pixels[x, y] = (0, 0, 0, 0)
                continue
            if alpha > 0.985:
                alpha = 1.0

            # Reverse compositing from subject-over-key to recover semi-transparent
            # glass, glow, antialiased edges, and sweep highlights.
            rr = (r - (1.0 - alpha) * kr) / alpha
            gg = (g - (1.0 - alpha) * kg) / alpha
            bb = (b - (1.0 - alpha) * kb) / alpha
            rr = max(0.0, min(255.0, rr))
            gg = max(0.0, min(255.0, gg))
            bb = max(0.0, min(255.0, bb))

            # Magenta despill. Reduce red only when a purple fringe is stronger
            # than the recovered green channel; keep cyan glass and warm handle.
            magenta_excess = min(rr, bb) - gg
            if magenta_excess > 5:
                rr = max(0.0, rr - magenta_excess * 0.9)
                bb = max(0.0, bb - magenta_excess * 0.15)

            pixels[x, y] = (clamp(rr), clamp(gg), clamp(bb), clamp(alpha * 255))

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


def is_key_background_pixel(pixel: tuple[int, int, int, int], key: tuple[int, int, int]) -> bool:
    r, g, b, a = pixel
    if a == 0:
        return True

    kr, kg, kb = key
    distance = ((r - kr) ** 2 + (g - kg) ** 2 + (b - kb) ** 2) ** 0.5
    magenta_like = r >= 175 and b >= 145 and g <= 125 and min(r, b) - g >= 55
    return distance <= 145 and magenta_like


def connected_key_background(image: Image.Image, key: tuple[int, int, int]) -> list[list[bool]]:
    width, height = image.size
    pixels = image.load()
    visited = [[False for _ in range(width)] for _ in range(height)]
    stack: list[tuple[int, int]] = []

    for x in range(width):
        stack.append((x, 0))
        stack.append((x, height - 1))
    for y in range(height):
        stack.append((0, y))
        stack.append((width - 1, y))

    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= width or y >= height or visited[y][x]:
            continue
        if not is_key_background_pixel(pixels[x, y], key):
            continue

        visited[y][x] = True
        stack.append((x + 1, y))
        stack.append((x - 1, y))
        stack.append((x, y + 1))
        stack.append((x, y - 1))

    return visited


def normalize_foreground(source: Path, output: Path, size: int, scale: float) -> None:
    image = Image.open(source).convert("RGBA")
    bbox = image.getbbox()
    if bbox is None:
        raise ValueError("No visible pixels after key removal")

    subject = image.crop(bbox)
    max_subject = max(1, int(round(size * scale)))
    subject.thumbnail((max_subject, max_subject), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    left = (size - subject.width) // 2
    top = (size - subject.height) // 2
    canvas.alpha_composite(subject, (left, top))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


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
    parser.add_argument("--alpha", required=True, type=Path)
    parser.add_argument("--final", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    parser.add_argument("--key", default="#ff00ff")
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--scale", type=float, default=0.70)
    args = parser.parse_args()

    key = parse_hex_color(args.key)
    remove_key(args.source, args.alpha, key)
    normalize_foreground(args.alpha, args.final, args.size, args.scale)
    checker_preview(args.final, args.preview)


if __name__ == "__main__":
    main()
