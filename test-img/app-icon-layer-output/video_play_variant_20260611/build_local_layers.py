from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
REF = ROOT / "reference.png"
SIZE = 512


def rounded_polygon_mask(points, radius=10, size=(SIZE, SIZE)):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(points, fill=255)
    if radius > 0:
        for x, y in points:
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(radius / 2))
        mask = mask.point(lambda p: 255 if p > 32 else 0)
    return mask


def make_checker(size=SIZE, cell=16):
    img = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)
    for y in range(0, size, cell):
        for x in range(0, size, cell):
            if (x // cell + y // cell) % 2:
                d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(210, 215, 225, 255))
    return img


def fit_square(img):
    img = img.convert("RGBA")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side)).resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def draw_background():
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    base = np.zeros((SIZE, SIZE, 3), dtype=np.float32)
    top = np.array([16, 13, 54], dtype=np.float32)
    bottom = np.array([30, 18, 78], dtype=np.float32)
    t = yy / (SIZE - 1)
    base[:] = top * (1 - t[..., None]) + bottom * t[..., None]

    glows = [
        (130, 190, 170, np.array([75, 55, 210]), 0.42),
        (402, 385, 210, np.array([255, 80, 185]), 0.48),
        (345, 205, 190, np.array([126, 55, 190]), 0.30),
        (105, 455, 150, np.array([42, 82, 196]), 0.25),
    ]
    for cx, cy, sigma, color, strength in glows:
        dist2 = (xx - cx) ** 2 + (yy - cy) ** 2
        g = np.exp(-dist2 / (2 * sigma * sigma))[..., None]
        base = base * (1 - g * strength) + color * (g * strength)

    arr = np.clip(base, 0, 255).astype(np.uint8)
    bg = Image.fromarray(arr, "RGB").convert("RGBA")
    d = ImageDraw.Draw(bg, "RGBA")

    # Abstract lower film-like waves, kept as background decoration only.
    d.arc((-70, 285, 330, 660), 202, 355, fill=(88, 52, 190, 95), width=18)
    d.arc((275, 255, 655, 650), 190, 342, fill=(245, 74, 166, 85), width=18)
    d.arc((260, 320, 620, 710), 190, 330, fill=(255, 151, 190, 50), width=34)

    for x, y, r, color in [
        (449, 132, 18, (255, 121, 218, 210)),
        (71, 240, 4, (135, 96, 255, 185)),
        (392, 354, 3, (255, 103, 140, 170)),
        (318, 398, 2, (186, 92, 230, 125)),
        (231, 461, 3, (198, 80, 231, 150)),
    ]:
        d.ellipse((x - r, y - r, x + r, y + r), fill=color)
        d.ellipse((x - r * 3, y - r * 3, x + r * 3, y + r * 3), fill=color[:3] + (35,))

    # Star sparkle.
    cx, cy = 452, 132
    d.polygon([(cx, cy - 17), (cx + 6, cy - 4), (cx + 18, cy), (cx + 6, cy + 4), (cx, cy + 17), (cx - 6, cy + 4), (cx - 18, cy), (cx - 6, cy - 4)], fill=(255, 142, 226, 205))
    return bg.convert("RGB")


def draw_subject_mask():
    mask = Image.new("L", (SIZE, SIZE), 0)
    d = ImageDraw.Draw(mask)

    # Main film body and side towers.
    d.rounded_rectangle((73, 134, 446, 384), radius=58, fill=255)
    d.rounded_rectangle((124, 169, 391, 368), radius=35, fill=255)
    d.rounded_rectangle((74, 137, 146, 385), radius=34, fill=255)
    d.rounded_rectangle((407, 150, 446, 374), radius=24, fill=255)

    # Diagonal clapper slate.
    slate = [(92, 140), (417, 57), (430, 96), (136, 167)]
    mask = Image.composite(Image.new("L", (SIZE, SIZE), 255), mask, rounded_polygon_mask(slate, 13))

    # Large rounded play triangle approximated by a thick polygon with softened corners.
    tri = [(165, 151), (166, 398), (396, 281)]
    play_mask = rounded_polygon_mask(tri, 38)
    mask = Image.composite(Image.new("L", (SIZE, SIZE), 255), mask, play_mask)

    # Lower film ribbons as thick curves.
    d = ImageDraw.Draw(mask)
    d.line([(20, 350), (97, 330), (170, 371), (251, 455), (331, 501)], fill=255, width=58, joint="curve")
    d.line([(328, 486), (376, 407), (445, 360), (504, 333)], fill=255, width=66, joint="curve")

    mask = mask.filter(ImageFilter.GaussianBlur(1.8))
    return mask


def alpha_from_mask(ref, mask):
    # Keep fine glow/detail from the reference inside the geometric mask.
    arr = np.asarray(ref.convert("RGB"), dtype=np.float32)
    lum = arr[..., 0] * 0.299 + arr[..., 1] * 0.587 + arr[..., 2] * 0.114
    m = np.asarray(mask, dtype=np.float32)
    alpha = np.maximum(m, np.clip((lum - 18) * 4.5, 0, 255) * (m > 4))
    alpha = Image.fromarray(np.clip(alpha, 0, 255).astype(np.uint8), "L")
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.6))
    out = ref.copy()
    out.putalpha(alpha)
    return out


def scale_subject_to_70(img):
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    subject = img.crop(bbox)
    w, h = subject.size
    max_dim = int(SIZE * 0.70)
    scale = min(max_dim / w, max_dim / h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    subject = subject.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.alpha_composite(subject, ((SIZE - nw) // 2, (SIZE - nh) // 2))
    return canvas


def draw_negative():
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    white = (255, 255, 255, 255)
    clear = (0, 0, 0, 0)

    # White subject scaffold.
    d.rounded_rectangle((73, 134, 446, 384), radius=58, fill=white)
    d.rounded_rectangle((74, 137, 146, 385), radius=34, fill=white)
    d.rounded_rectangle((407, 150, 446, 374), radius=24, fill=white)
    d.polygon([(92, 140), (417, 57), (430, 96), (136, 167)], fill=white)
    d.line([(34, 350), (100, 333), (170, 371), (251, 452), (328, 486)], fill=white, width=54, joint="curve")
    d.line([(334, 476), (379, 407), (443, 362), (484, 342)], fill=white, width=60, joint="curve")
    d.polygon([(165, 151), (166, 398), (396, 281)], fill=white)
    d.ellipse((142, 128, 198, 184), fill=white)
    d.ellipse((142, 366, 198, 422), fill=white)
    d.ellipse((368, 253, 424, 309), fill=white)

    # Transparent identity holes: viewing window, film perforations, clapper stripes.
    d.rounded_rectangle((121, 169, 392, 368), radius=35, fill=clear)
    d.polygon([(184, 178), (181, 360), (364, 281)], fill=white)
    for y in [187, 222, 258, 294, 330]:
        d.rounded_rectangle((89, y, 108, y + 20), radius=4, fill=clear)
    for y in [181, 220, 258, 296, 334]:
        d.rounded_rectangle((420, y, 441, y + 22), radius=5, fill=clear)
    for x in [202, 252, 304, 355]:
        d.polygon([(x, 108), (x + 31, 100), (x + 12, 138), (x - 21, 146)], fill=clear)
    for x, y in [(61, 403), (105, 421), (153, 446), (407, 382), (450, 361), (468, 345)]:
        d.rounded_rectangle((x, y, x + 28, y + 16), radius=3, fill=clear)

    # Clean and resize whole canvas to 72x72 as required.
    img = img.filter(ImageFilter.GaussianBlur(0.45))
    a = img.getchannel("A").point(lambda p: 255 if p > 80 else 0)
    img.putalpha(a)
    visible = Image.new("RGBA", (512, 512), white)
    visible.putalpha(a)
    visible = visible.resize((72, 72), Image.Resampling.LANCZOS)
    edge_alpha = visible.getchannel("A")
    edge_draw = ImageDraw.Draw(edge_alpha)
    edge_draw.rectangle((0, 0, 71, 0), fill=0)
    edge_draw.rectangle((0, 71, 71, 71), fill=0)
    edge_draw.rectangle((0, 0, 0, 71), fill=0)
    edge_draw.rectangle((71, 0, 71, 71), fill=0)
    visible.putalpha(edge_alpha.point(lambda p: 255 if p > 80 else 0))
    return visible


def save_checker_preview(fg, path):
    checker = make_checker()
    checker.alpha_composite(fg)
    checker.save(path)


def contact_sheet(paths, out):
    thumbs = []
    labels = []
    for label, path in paths:
        im = Image.open(path).convert("RGBA")
        if im.size != (160, 160):
            im.thumbnail((160, 160), Image.Resampling.LANCZOS)
        cell = Image.new("RGBA", (180, 198), (245, 247, 250, 255))
        cell.alpha_composite(im, ((180 - im.width) // 2, 10))
        draw = ImageDraw.Draw(cell)
        draw.text((10, 174), label, fill=(28, 32, 44, 255), font=ImageFont.load_default())
        thumbs.append(cell)
    sheet = Image.new("RGBA", (180 * len(thumbs), 198), (232, 236, 242, 255))
    for i, thumb in enumerate(thumbs):
        sheet.alpha_composite(thumb, (i * 180, 0))
    sheet.save(out)


def main():
    ref = fit_square(Image.open(REF))
    bg = draw_background()
    mask = draw_subject_mask()
    fg_full = alpha_from_mask(ref, mask)
    fg_70 = scale_subject_to_70(fg_full)
    negative = draw_negative()

    bg.save(ROOT / "video_play_background_512.png")
    fg_full.save(ROOT / "video_play_foreground_full_512.png")
    fg_70.save(ROOT / "video_play_foreground_70pct_512.png")
    negative.save(ROOT / "video_play_white_negative_72.png")
    save_checker_preview(fg_full, ROOT / "video_play_foreground_full_checker.png")
    save_checker_preview(fg_70, ROOT / "video_play_foreground_70pct_checker.png")

    composite = bg.convert("RGBA")
    composite.alpha_composite(fg_full)
    composite.save(ROOT / "video_play_composite_full_subject_preview.png")

    contact_sheet(
        [
            ("foreground 70%", ROOT / "video_play_foreground_70pct_512.png"),
            ("background", ROOT / "video_play_background_512.png"),
            ("negative 72", ROOT / "video_play_white_negative_72.png"),
            ("full preview", ROOT / "video_play_composite_full_subject_preview.png"),
        ],
        ROOT / "video_play_contact_sheet.png",
    )


if __name__ == "__main__":
    main()
