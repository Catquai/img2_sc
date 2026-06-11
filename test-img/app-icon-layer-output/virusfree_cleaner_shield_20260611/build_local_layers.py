from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).parent
SIZE = 512
SCALE = 4


def lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


def make_background() -> None:
    s = SIZE * SCALE
    image = Image.new("RGB", (s, s))
    pixels = image.load()

    for y in range(s):
        for x in range(s):
            nx = x / s
            ny = y / s
            radial = max(0.0, 1.0 - math.hypot(nx - 0.53, ny - 0.46) / 0.72)
            diagonal = (nx + (1.0 - ny)) * 0.5
            r = lerp(20, 82, radial * 0.72 + diagonal * 0.12)
            g = lerp(79, 159, radial * 0.72 + diagonal * 0.15)
            b = lerp(210, 255, radial * 0.55 + diagonal * 0.16)
            pixels[x, y] = (r, g, b)

    glow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    center = (round(s * 0.53), round(s * 0.45))
    for radius, alpha in [(740, 16), (590, 22), (450, 28)]:
        gd.ellipse(
            (
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
            ),
            fill=(150, 215, 255, alpha),
        )
    glow = glow.filter(ImageFilter.GaussianBlur(150))
    image = Image.alpha_composite(image.convert("RGBA"), glow)

    rings = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rings)
    cx, cy = round(s * 0.5), round(s * 0.5)
    for radius, width, alpha in [(820, 8, 26), (690, 6, 34), (530, 4, 20)]:
        rd.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            outline=(190, 226, 255, alpha),
            width=width,
        )

    tick_radius = 760
    for i in range(120):
        angle = math.tau * i / 120
        length = 34 if i % 5 == 0 else 22
        x1 = cx + math.cos(angle) * tick_radius
        y1 = cy + math.sin(angle) * tick_radius
        x2 = cx + math.cos(angle) * (tick_radius + length)
        y2 = cy + math.sin(angle) * (tick_radius + length)
        rd.line((x1, y1, x2, y2), fill=(225, 243, 255, 130), width=4)

    for i in range(18):
        angle = math.tau * (i / 18 + 0.015)
        radius = 880 + (i % 3) * 45
        x = cx + math.cos(angle) * radius
        y = cy + math.sin(angle) * radius
        r = 5 + (i % 3) * 2
        rd.ellipse((x - r, y - r, x + r, y + r), fill=(225, 246, 255, 70))

    image = Image.alpha_composite(image, rings)
    image.resize((SIZE, SIZE), Image.Resampling.LANCZOS).convert("RGB").save(
        ROOT / "virusfree_background_512.png"
    )


def make_negative_from_keyed() -> None:
    source = Image.open(ROOT / "virusfree_foreground_keyed_source.png").convert("RGB")
    source = source.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    negative = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    src = source.load()
    out = negative.load()

    for y in range(SIZE):
        for x in range(SIZE):
            r, g, b = src[x, y]
            is_magenta = r > 160 and b > 145 and g < 125 and min(r, b) - g > 55
            if is_magenta:
                continue

            # Keep the pearly shield frame and broom as white fill. The blue
            # shield face becomes transparent negative space between them.
            whiteness = min(r, g, b)
            blue_dominance = b - r
            is_white_structure = whiteness > 178 and abs(r - g) < 55 and abs(g - b) < 70
            is_bright_ice = r > 155 and g > 170 and b > 188
            is_blue_face = b > 150 and blue_dominance > 45 and r < 150
            if (is_white_structure or is_bright_ice) and not is_blue_face:
                out[x, y] = (255, 255, 255, 255)

    negative.save(ROOT / "virusfree_negative_source_512.png")
    negative.resize((72, 72), Image.Resampling.LANCZOS).save(
        ROOT / "virusfree_negative_72_precheck.png"
    )


if __name__ == "__main__":
    make_background()
    make_negative_from_keyed()
