"""Joins the two official Strava images into one header logo (symbol + wordmark, side by side).
Run once from the Strava folder:   py make_logo.py
"""
from pathlib import Path
from PIL import Image

ASSETS = Path("app/assets")
ORANGE = (252, 76, 2)        # Strava orange #FC4C02
HEIGHT = 120                 # pixels; the app shrinks it to the size we choose in CSS
WORD_SIZE = 0.42             # wordmark height compared with the symbol (make bigger/smaller if needed)
GAP = 0.22                   # space between symbol and wordmark


def clean(path):
    """White background -> transparent, keep the soft edges, trim the empty border."""
    src = Image.open(path).convert("RGBA")
    img = Image.new("RGBA", src.size, "white")
    img.alpha_composite(src)                              # works for white-background and transparent files
    img = img.convert("RGB")
    out = Image.new("RGBA", img.size)
    px, opx = img.load(), out.load()
    for x in range(img.width):
        for y in range(img.height):
            blue = px[x, y][2]                              # orange has almost no blue, white has full blue
            alpha = max(0, min(255, round((255 - blue) * 255 / 253)))
            opx[x, y] = ORANGE + (alpha,)
    return out.crop(out.getbbox())


def to_height(img, h):
    return img.resize((round(img.width * h / img.height), h), Image.LANCZOS)


symbol = to_height(clean(ASSETS / "strava_symbol.png"), HEIGHT)
word = to_height(clean(ASSETS / "strava_wordmark.png"), round(HEIGHT * WORD_SIZE))
gap = round(HEIGHT * GAP)

logo = Image.new("RGBA", (symbol.width + gap + word.width, HEIGHT), (0, 0, 0, 0))
logo.alpha_composite(symbol, (0, 0))
logo.alpha_composite(word, (symbol.width + gap, (HEIGHT - word.height) // 2))
logo.save(ASSETS / "strava_header_logo.png")
symbol.save(ASSETS / "strava_icon.png")
print("Saved:", logo.size, "->", ASSETS / "strava_header_logo.png")