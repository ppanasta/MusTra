"""Draw the MusTra app icons (web app and Android launcher). Needs Pillow.

    python mobile/make_icons.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
PURPLE, PURPLE_DARK, WHITE = (106, 63, 160), (75, 42, 120), (255, 255, 255)
FONTS = ["DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "Arial Bold.ttf", "arialbd.ttf"]


def font(size):
    for name in FONTS:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw(size, padding=0.0, rounded=True):
    """Purple tile with 'Mu' over a small staff line: MusTra's monogram."""
    scale = 4
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    radius = int(s * 0.22) if rounded else 0
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=radius, fill=PURPLE)
    inner = s * (1 - 2 * padding)
    off = s * padding
    f = font(int(inner * 0.42))
    text = "Mu"
    box = d.textbbox((0, 0), text, font=f)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text((off + (inner - w) / 2 - box[0], off + inner * 0.40 - h / 2 - box[1]), text, font=f, fill=WHITE)
    # three staff lines with a quarter-tone "neutral" mark: the 'Tra(nslations)'
    for i in range(3):
        y = off + inner * (0.70 + i * 0.065)
        d.rounded_rectangle([off + inner * 0.2, y, off + inner * 0.8, y + inner * 0.022],
                            radius=int(inner * 0.011), fill=(233, 223, 247))
    cx, cy = off + inner * 0.62, off + inner * 0.735
    r = inner * 0.055
    d.ellipse([cx - r * 1.25, cy - r, cx + r * 1.25, cy + r], fill=WHITE, outline=PURPLE_DARK,
              width=max(1, int(inner * 0.008)))
    return img.resize((size, size), Image.LANCZOS)


def main():
    web = ROOT / "web" / "icons"
    web.mkdir(parents=True, exist_ok=True)
    draw(192).save(web / "icon-192.png")
    draw(512).save(web / "icon-512.png")
    draw(512, padding=0.1, rounded=False).save(web / "icon-maskable-512.png")
    flat = Image.new("RGB", (180, 180), PURPLE)
    flat.paste(draw(180, rounded=False), (0, 0), draw(180, rounded=False))
    flat.save(web / "apple-touch-icon.png")   # iOS rounds the corners itself
    res = ROOT / "android" / "app" / "src" / "main" / "res"
    for name, px in {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}.items():
        folder = res / f"mipmap-{name}"
        folder.mkdir(parents=True, exist_ok=True)
        draw(px).save(folder / "ic_launcher.png")
    print("Icons written.")


if __name__ == "__main__":
    main()
