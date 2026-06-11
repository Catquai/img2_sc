from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


OUT = Path("generated_clean_icon_variants")
SCALE = 4


def rgba(hex_color, alpha=255):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def lerp(a, b, t):
    return int(a + (b - a) * t)


def gradient(size, top, bottom, radius):
    w, h = size
    top = rgba(top)
    bottom = rgba(bottom)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(lerp(top[i], bottom[i], t) for i in range(4))
        for x in range(w):
            px[x, y] = c
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
    img.putalpha(mask)
    return img


def downsample(img, size):
    return img.resize(size, Image.Resampling.LANCZOS)


def rr(draw, box, r, fill):
    draw.rounded_rectangle(tuple(int(v) for v in box), radius=int(r), fill=fill)


def poly(draw, points, fill):
    draw.polygon([(int(x), int(y)) for x, y in points], fill=fill)


def save_icon(name, base_size, bg_top, bg_bottom, draw_symbol):
    W = H = base_size * SCALE
    img = gradient((W, H), bg_top, bg_bottom, int(W * 0.26))
    soft = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(soft)
    sd.ellipse((int(W * .12), int(H * .07), int(W * .88), int(H * .92)), fill=(255, 255, 255, 23))
    soft = soft.filter(ImageFilter.GaussianBlur(int(W * .065)))
    img.alpha_composite(soft)
    draw_symbol(img, W, H)
    img = downsample(img, (base_size, base_size))
    OUT.mkdir(exist_ok=True)
    img.save(OUT / name)


def folder_symbol(img, W, H):
    d = ImageDraw.Draw(img)
    # New variation: more compact folder with tab and inner lip, keeping big-file/folder identity.
    rr(d, (W * .17, H * .27, W * .83, H * .75), W * .105, rgba("#fff2b0", 245))
    rr(d, (W * .17, H * .33, W * .83, H * .79), W * .09, rgba("#ffd15b", 235))
    rr(d, (W * .17, H * .27, W * .47, H * .43), W * .085, rgba("#fff5c7", 250))
    d.rectangle((W * .25, H * .37, W * .80, H * .44), fill=rgba("#fff2b0", 245))
    rr(d, (W * .24, H * .48, W * .76, H * .68), W * .045, rgba("#ffe98f", 154))


def android_symbol(img, W, H):
    d = ImageDraw.Draw(img)
    rr(d, (W * .26, H * .30, W * .74, H * .77), W * .18, rgba("#c7ff8a", 225))
    d.rectangle((W * .26, H * .48, W * .74, H * .76), fill=rgba("#b6f56f", 225))
    d.line((W * .35, H * .25, W * .28, H * .15), fill=rgba("#d9ffba", 245), width=int(W * .035))
    d.line((W * .65, H * .25, W * .73, H * .15), fill=rgba("#d9ffba", 245), width=int(W * .035))
    d.ellipse((W * .38, H * .34, W * .45, H * .41), fill=rgba("#19c84f", 235))
    d.ellipse((W * .57, H * .34, W * .64, H * .41), fill=rgba("#19c84f", 235))
    d.line((W * .29, H * .51, W * .71, H * .51), fill=rgba("#64dd58", 125), width=int(W * .025))


def image_symbol(img, W, H):
    d = ImageDraw.Draw(img)
    rr(d, (W * .20, H * .20, W * .80, H * .80), W * .13, rgba("#b8ffc9", 232))
    rr(d, (W * .28, H * .28, W * .72, H * .72), W * .055, rgba("#51df6e", 225))
    poly(d, [(W * .31, H * .67), (W * .45, H * .48), (W * .56, H * .60), (W * .63, H * .53), (W * .71, H * .67)], rgba("#28cf55", 255))
    rr(d, (W * .61, H * .34, W * .70, H * .43), W * .04, rgba("#30d659", 255))
    rr(d, (W * .34, H * .38, W * .57, H * .68), W * .03, rgba("#24d760", 218))


def video_symbol(img, W, H):
    d = ImageDraw.Draw(img)
    rr(d, (W * .20, H * .21, W * .80, H * .79), W * .14, rgba("#c1efff", 226))
    rr(d, (W * .28, H * .29, W * .72, H * .71), W * .075, rgba("#9edfff", 172))
    poly(d, [(W * .43, H * .39), (W * .43, H * .61), (W * .62, H * .50)], rgba("#20acd8", 255))
    d.ellipse((W * .37, H * .33, W * .66, H * .66), outline=rgba("#74d6f2", 92), width=int(W * .035))


def cleanup_symbol(img, W, H):
    d = ImageDraw.Draw(img)
    rr(d, (W * .31, H * .36, W * .69, H * .77), W * .055, rgba("#ceff8b", 230))
    rr(d, (W * .23, H * .29, W * .77, H * .37), W * .04, rgba("#dfffba", 245))
    rr(d, (W * .40, H * .22, W * .60, H * .32), W * .05, rgba("#eaffc9", 245))
    d.rectangle((W * .37, H * .39, W * .63, H * .67), fill=rgba("#b7f070", 195))
    d.line((W * .36, H * .65, W * .64, H * .65), fill=rgba("#4acb47", 210), width=int(W * .045))


save_icon("notif_bigfile_variant.png", 108, "#fff83c", "#ffa826", folder_symbol)
save_icon("notif_ic_app_variant.png", 108, "#82ff9b", "#48df64", android_symbol)
save_icon("icon_image_variant.png", 120, "#8dffa1", "#46de68", image_symbol)
save_icon("icon_tt_clean_video_variant.png", 120, "#42e8f2", "#28a8e8", video_symbol)
save_icon("notif_ic_cleanup_variant.png", 108, "#79ff99", "#49df66", cleanup_symbol)
