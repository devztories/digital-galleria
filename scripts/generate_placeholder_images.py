"""Create simple PLACEHOLDER pictures for every slot listed in products/catalog_data.py.

    python scripts/generate_placeholder_images.py            # fill only missing files
    python scripts/generate_placeholder_images.py --force    # redraw everything

Needs Pillow (already in requirements.txt). Existing files are never touched
unless --force is given, so real photos you drop in later are safe.
Replace the generated files with real product photos keeping the same
names/paths — nothing else has to change.
"""
import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "products"))
import catalog_data as data  # noqa: E402  (pure-python module, no Django needed)

CATALOG = ROOT / "static" / "image_library"   # ONE flat folder
SIZE = 900
CREAM = (250, 246, 238)


def slugify(text):
    out = "".join(c.lower() if c.isalnum() else "-" for c in text)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def luminance(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def font(size, bold=False):
    for name in ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


# ---------------------------------------------------------------- shapes ---
def photo(d, box, seed=0):
    """A tiny landscape 'photo' used inside frames, mugs, puzzles."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(176, 208, 232))
    h = y1 - y0
    d.rectangle((x0, y0 + h * 0.62, x1, y1), fill=(112, 160, 104))
    d.ellipse((x0 + (x1 - x0) * 0.62, y0 + h * 0.12, x0 + (x1 - x0) * 0.84, y0 + h * 0.12 + (x1 - x0) * 0.22), fill=(250, 214, 110))
    d.polygon([(x0, y0 + h * 0.62), (x0 + (x1 - x0) * 0.3, y0 + h * 0.3), (x0 + (x1 - x0) * 0.6, y0 + h * 0.62)], fill=(96, 138, 92))


def draw_frame(d, cx, cy, s, col, w=520, h=640):
    w, h = w * s, h * s
    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    d.rounded_rectangle(box, radius=10 * s, fill=col)
    d.rounded_rectangle([box[0] + 6 * s, box[1] + 6 * s, box[2] - 6 * s, box[3] - 6 * s], radius=6 * s, outline=mix(col, (255, 255, 255), 0.35), width=max(1, int(3 * s)))
    m = 44 * s
    d.rectangle([box[0] + m, box[1] + m, box[2] - m, box[3] - m], fill=CREAM)
    m2 = 80 * s
    photo(d, [box[0] + m2, box[1] + m2, box[2] - m2, box[3] - m2])


def draw_canvas(d, cx, cy, s, col):
    w, h = 600 * s, 460 * s
    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    d.rectangle((box[0] + 10 * s, box[1] + 10 * s, box[2] + 10 * s, box[3] + 10 * s), fill=mix(col, (0, 0, 0), 0.55))
    d.rectangle(box, fill=mix(col, (255, 255, 255), 0.82))
    d.ellipse((cx - 230 * s, cy - 160 * s, cx + 40 * s, cy + 110 * s), fill=col)
    d.ellipse((cx - 20 * s, cy - 40 * s, cx + 230 * s, cy + 190 * s), fill=mix(col, (255, 255, 255), 0.45))
    d.pieslice((cx - 260 * s, cy - 40 * s, cx + 90 * s, cy + 310 * s), 180, 270, fill=mix(col, (0, 0, 0), 0.35))
    d.line((cx - 260 * s, cy + 150 * s, cx + 260 * s, cy - 120 * s), fill=mix(col, (0, 0, 0), 0.6), width=max(2, int(6 * s)))


def draw_collage(d, cx, cy, s, col):
    cells = [(-190, -170, 200, 260), (40, -170, 170, 170), (-190, 120, 200, 150), (40, 20, 170, 250), (260, -170, 150, 200), (260, 60, 150, 210)]
    for (ox, oy, w, h) in cells:
        x, y = cx + (ox - 40) * s, cy + oy * s * 0.9
        d.rectangle((x, y, x + w * s, y + h * s), fill=col)
        d.rectangle((x + 8 * s, y + 8 * s, x + (w - 8) * s, y + (h - 8) * s), fill=CREAM)
        photo(d, (x + 18 * s, y + 18 * s, x + (w - 18) * s, y + (h - 18) * s))


def draw_clock(d, cx, cy, s, col):
    r = 270 * s
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    d.ellipse((cx - r + 26 * s, cy - r + 26 * s, cx + r - 26 * s, cy + r - 26 * s), fill=CREAM)
    for i in range(12):
        a = math.radians(i * 30)
        d.line((cx + math.sin(a) * (r - 60 * s), cy - math.cos(a) * (r - 60 * s), cx + math.sin(a) * (r - 40 * s), cy - math.cos(a) * (r - 40 * s)), fill=col, width=max(2, int(8 * s)))
    d.line((cx, cy, cx + 80 * s, cy - 90 * s), fill=col, width=max(3, int(14 * s)))
    d.line((cx, cy, cx - 30 * s, cy - 150 * s), fill=col, width=max(3, int(10 * s)))
    d.ellipse((cx - 14 * s, cy - 14 * s, cx + 14 * s, cy + 14 * s), fill=(214, 174, 85))


def draw_vase(d, cx, cy, s, col):
    stem = mix(col, (60, 90, 50), 0.6)
    for dx, top in ((-70, -330), (0, -380), (80, -310)):
        d.line((cx + dx * 0.2 * s, cy - 150 * s, cx + dx * s, cy + top * s * 0.55 - 40 * s), fill=stem, width=max(2, int(7 * s)))
        d.ellipse((cx + dx * s - 34 * s, cy + top * s * 0.55 - 74 * s, cx + dx * s + 34 * s, cy + top * s * 0.55 - 6 * s), fill=mix(col, (255, 255, 255), 0.55))
    d.rounded_rectangle((cx - 50 * s, cy - 160 * s, cx + 50 * s, cy - 40 * s), radius=24 * s, fill=col)
    d.ellipse((cx - 170 * s, cy - 140 * s, cx + 170 * s, cy + 270 * s), fill=col)
    d.ellipse((cx - 120 * s, cy - 60 * s, cx - 40 * s, cy + 60 * s), fill=mix(col, (255, 255, 255), 0.25))
    d.rectangle((cx - 110 * s, cy + 215 * s, cx + 110 * s, cy + 255 * s), fill=mix(col, (0, 0, 0), 0.25))


def draw_mug(d, cx, cy, s, col):
    w, h = 340 * s, 380 * s
    d.ellipse((cx + w / 2 - 50 * s, cy - 110 * s, cx + w / 2 + 130 * s, cy + 90 * s), outline=col, width=max(4, int(34 * s)))
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=36 * s, fill=col)
    d.rectangle((cx - w / 2 + 30 * s, cy - h / 2 + 90 * s, cx + w / 2 - 30 * s, cy + h / 2 - 70 * s), fill=CREAM)
    photo(d, (cx - w / 2 + 44 * s, cy - h / 2 + 104 * s, cx + w / 2 - 44 * s, cy + h / 2 - 84 * s))
    d.ellipse((cx - w / 2, cy - h / 2 - 22 * s, cx + w / 2, cy - h / 2 + 30 * s), fill=mix(col, (255, 255, 255), 0.3))


def draw_puzzle(d, cx, cy, s, col):
    w, h = 560 * s, 420 * s
    x0, y0 = cx - w / 2, cy - h / 2
    photo(d, (x0, y0, x0 + w, y0 + h))
    cols, rows = 5, 4
    for i in range(1, cols):
        x = x0 + w * i / cols
        d.line((x, y0, x, y0 + h), fill=CREAM, width=max(2, int(4 * s)))
    for j in range(1, rows):
        y = y0 + h * j / rows
        d.line((x0, y, x0 + w, y), fill=CREAM, width=max(2, int(4 * s)))
    for i in range(1, cols):
        for j in range(rows):
            if (i + j) % 2:
                x, y = x0 + w * i / cols, y0 + h * (j + 0.5) / rows
                d.ellipse((x - 14 * s, y - 14 * s, x + 14 * s, y + 14 * s), fill=CREAM)
    d.rectangle((x0, y0, x0 + w, y0 + h), outline=(120, 90, 160), width=max(2, int(6 * s)))


def draw_keychain(d, cx, cy, s, col):
    d.ellipse((cx - 110 * s, cy - 330 * s, cx + 110 * s, cy - 110 * s), outline=mix(col, (90, 90, 90), 0.3), width=max(3, int(16 * s)))
    d.rounded_rectangle((cx - 150 * s, cy - 130 * s, cx + 150 * s, cy + 250 * s), radius=60 * s, fill=col)
    d.ellipse((cx - 22 * s, cy - 100 * s, cx + 22 * s, cy - 56 * s), fill=CREAM)
    ink = mix(col, (0, 0, 0), 0.55)
    for i, wd in enumerate((150, 110, 130)):
        y = cy + (20 + i * 54) * s
        d.rounded_rectangle((cx - wd / 2 * s, y, cx + wd / 2 * s, y + 18 * s), radius=9 * s, fill=ink)


DRAW = {"frame": draw_frame, "canvas": draw_canvas, "collage": draw_collage, "clock": draw_clock,
        "vase": draw_vase, "mug": draw_mug, "puzzle": draw_puzzle, "keychain": draw_keychain}


# ----------------------------------------------------------------- images --
def render(kind, colour_hex, title, subtitle, view):
    col = hex_rgb(colour_hex)
    light = luminance(col) > 150
    bg1 = mix(col, (255, 255, 255), 0.88)
    bg2 = mix(col, (255, 255, 255), 0.7)
    img = Image.new("RGB", (SIZE, SIZE), bg1)
    d = ImageDraw.Draw(img)
    # soft vertical gradient
    for y in range(SIZE):
        d.line((0, y, SIZE, y), fill=mix(bg1, bg2, y / SIZE))
    # "table" strip
    d.rectangle((0, SIZE * 0.82, SIZE, SIZE), fill=mix(bg2, (0, 0, 0), 0.06))

    fn = DRAW[kind]
    draw_col = mix(col, (60, 60, 60), 0.25) if light else col
    if view == 1:      # front, centred
        d.ellipse((SIZE * 0.2, SIZE * 0.78, SIZE * 0.8, SIZE * 0.86), fill=mix(bg2, (0, 0, 0), 0.12))
        fn(d, SIZE / 2, SIZE * 0.47, 1.0, draw_col)
    elif view == 2:    # smaller, with decorative circles (lifestyle feel)
        d.ellipse((-120, -120, 330, 330), fill=mix(bg2, (255, 255, 255), 0.4))
        d.ellipse((SIZE - 260, SIZE * 0.15, SIZE + 90, SIZE * 0.15 + 350), fill=mix(bg2, (0, 0, 0), 0.05))
        fn(d, SIZE * 0.55, SIZE * 0.5, 0.78, draw_col)
    else:              # close-up detail
        fn(d, SIZE * 0.5, SIZE * 0.52, 1.45, draw_col)

    # caption
    ink = (45, 30, 60)
    d.rounded_rectangle((28, 28, 28 + 20 + len(title) * 15, 78), radius=14, fill=(255, 255, 255))
    d.text((40, 38), title, fill=ink, font=font(26, True))
    sub = f"{subtitle}  ·  view {view}"
    d.text((34, SIZE - 70), sub, fill=ink, font=font(24))
    d.text((34, SIZE - 38), "placeholder - replace with real photo", fill=mix(ink, (255, 255, 255), 0.4), font=font(18))
    return img


def cover(name, color):
    col = hex_rgb(color)
    img = Image.new("RGB", (1200, 800), mix(col, (255, 255, 255), 0.85))
    d = ImageDraw.Draw(img)
    for y in range(800):
        d.line((0, y, 1200, y), fill=mix(mix(col, (255, 255, 255), 0.85), mix(col, (255, 255, 255), 0.55), y / 800))
    d.ellipse((780, -140, 1380, 460), fill=mix(col, (255, 255, 255), 0.4))
    d.ellipse((-160, 420, 420, 1000), fill=mix(col, (255, 255, 255), 0.55))
    d.text((70, 560), name, fill=(45, 30, 60), font=font(86, True))
    d.text((74, 680), "category cover - placeholder, replace with real image", fill=(90, 70, 110), font=font(26))
    return img


COVER_STYLE = {
    "Photo Frames": ("frame", "#8E6BB5"), "Wall Art": ("canvas", "#1F6F9F"), "Home Decor": ("vase", "#B5573A"),
    "Gifts": ("mug", "#C0392B"), "Accessories": ("keychain", "#D6AE55"),
}


def save(img, path, force):
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "WEBP", quality=78, method=6)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    args = ap.parse_args()
    made = 0

    for name, _order in data.CATEGORIES:
        kind, colour = COVER_STYLE.get(name, ("frame", "#8E6BB5"))
        img = cover(name, colour)
        d = ImageDraw.Draw(img)
        DRAW[kind](d, 930, 330, 0.62, hex_rgb(colour))
        made += save(img, CATALOG / f"{slugify(name)}__cover.webp", args.force)

    for p in data.PRODUCTS:
        cat = slugify(p["category"])
        if p["colours"]:
            for cname in p["colours"]:
                for view in range(1, data.IMAGES_PER_COLOUR + 1):
                    img = render(p["kind"], data.COLOURS[cname], p["name"], cname, view)
                    made += save(img, CATALOG / f"{cat}__{p['slug']}__{slugify(cname)}__{view}.webp", args.force)
        else:
            for view in range(1, data.IMAGES_PER_COLOUR + 1):
                img = render(p["kind"], "#8E6BB5", p["name"], "Default", view)
                made += save(img, CATALOG / f"{cat}__{p['slug']}__{view}.webp", args.force)
    print(f"{made} image file(s) written under {CATALOG}")


if __name__ == "__main__":
    main()
