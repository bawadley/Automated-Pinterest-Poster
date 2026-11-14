from pathlib import Path
import hashlib
import textwrap
import yaml
from PIL import Image, ImageDraw, ImageFont

from models import PinDraft


WIDTH = 1000
HEIGHT = 1500


def load_tip_config(path="tip_config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _font(size, bold=False):
    candidates = []
    if bold:
        candidates.extend([
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ])
    else:
        candidates.extend([
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ])

    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)

    return ImageFont.load_default()


def _wrap_for_width(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = []

    for word in words:
        trial = " ".join(current + [word])
        box = draw.textbbox((0, 0), trial, font=font)
        if box[2] - box[0] <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]

    if current:
        lines.append(" ".join(current))

    return lines


def _draw_wrapped(
    draw,
    text,
    font,
    x,
    y,
    max_width,
    line_gap=14,
    fill="black",
):
    lines = _wrap_for_width(draw, text, font, max_width)
    line_height = draw.textbbox((0, 0), "Ag", font=font)[3]
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height + line_gap
    return y


TIP_PALETTES = [
    {
        "background": "#F7E8C4",
        "panel": "#FFF8E8",
        "text": "#2B2118",
        "accent": "#C56A32",
    },
    {
        "background": "#DCEFE6",
        "panel": "#F4FBF7",
        "text": "#17362A",
        "accent": "#3C7A5F",
    },
    {
        "background": "#DDE8F6",
        "panel": "#F5F8FC",
        "text": "#1C2E4A",
        "accent": "#4D6FA9",
    },
    {
        "background": "#EFE1F3",
        "panel": "#FBF6FC",
        "text": "#402447",
        "accent": "#8A4E93",
    },
    {
        "background": "#F8DDD8",
        "panel": "#FFF5F3",
        "text": "#4A2520",
        "accent": "#B85C50",
    },
]

QUOTE_PALETTES = [
    {
        "background": "#243447",
        "panel": "#31465E",
        "text": "#FFF7E6",
        "accent": "#F2B84B",
    },
    {
        "background": "#4B365F",
        "panel": "#604879",
        "text": "#FFF8F2",
        "accent": "#F6C1D5",
    },
    {
        "background": "#1F4B45",
        "panel": "#2C625B",
        "text": "#F2FFF9",
        "accent": "#F0C96A",
    },
    {
        "background": "#6B3F2B",
        "panel": "#80523B",
        "text": "#FFF8ED",
        "accent": "#F1C27D",
    },
    {
        "background": "#2D4059",
        "panel": "#3C5777",
        "text": "#F9FBFF",
        "accent": "#F07B6A",
    },
]


def _pick_palette(item_id, palettes):
    digest = hashlib.sha256(str(item_id).encode("utf-8")).digest()
    return palettes[digest[0] % len(palettes)]


def render_tip_image(tip, category_name, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    palette = _pick_palette(tip["id"], TIP_PALETTES)
    image = Image.new("RGB", (WIDTH, HEIGHT), palette["background"])
    draw = ImageDraw.Draw(image)

    category_font = _font(34, bold=True)
    title_font = _font(72, bold=True)
    body_font = _font(38)
    bullet_font = _font(34)
    footer_font = _font(30, bold=True)

    margin = 90
    max_width = WIDTH - (margin * 2)

    draw.rounded_rectangle(
        (55, 55, WIDTH - 55, HEIGHT - 55),
        radius=38,
        fill=palette["panel"],
        outline=palette["accent"],
        width=8,
    )

    y = 110
    draw.text(
        (margin, y),
        category_name.upper(),
        font=category_font,
        fill=palette["accent"],
    )
    y += 85

    y = _draw_wrapped(
        draw,
        tip["headline"],
        title_font,
        margin,
        y,
        max_width,
        line_gap=20,
        fill=palette["text"],
    )

    y += 55
    draw.line(
        (margin, y, WIDTH - margin, y),
        fill=palette["accent"],
        width=5,
    )
    y += 55

    y = _draw_wrapped(
        draw,
        tip["body"],
        body_font,
        margin,
        y,
        max_width,
        line_gap=16,
        fill=palette["text"],
    )

    y += 45

    for bullet in tip.get("bullets", []):
        bullet_text = f"• {bullet}"
        y = _draw_wrapped(
            draw,
            bullet_text,
            bullet_font,
            margin,
            y,
            max_width,
            line_gap=12,
            fill=palette["text"],
        )
        y += 18

    footer = "SAVE THIS TIP FOR LATER"
    footer_box = draw.textbbox((0, 0), footer, font=footer_font)
    footer_width = footer_box[2] - footer_box[0]
    draw.rounded_rectangle(
        (
            (WIDTH - footer_width) / 2 - 28,
            HEIGHT - 175,
            (WIDTH + footer_width) / 2 + 28,
            HEIGHT - 105,
        ),
        radius=22,
        fill=palette["accent"],
    )
    draw.text(
        ((WIDTH - footer_width) / 2, HEIGHT - 157),
        footer,
        font=footer_font,
        fill=palette["panel"],
    )

    filename = f"{tip['id']}_pinterest.jpg"
    output_path = output_dir / filename
    image.save(output_path, format="JPEG", quality=95, optimize=True)
    return str(output_path.resolve())


def render_quote_image(tip, category_name, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    palette = _pick_palette(tip["id"], QUOTE_PALETTES)
    image = Image.new("RGB", (WIDTH, HEIGHT), palette["background"])
    draw = ImageDraw.Draw(image)

    category_font = _font(32, bold=True)
    quote_font = _font(64, bold=True)
    footer_font = _font(28, bold=True)
    quote_mark_font = _font(120, bold=True)

    margin = 105
    max_width = WIDTH - (margin * 2)

    draw.rounded_rectangle(
        (55, 55, WIDTH - 55, HEIGHT - 55),
        radius=42,
        fill=palette["panel"],
        outline=palette["accent"],
        width=8,
    )

    y = 120
    draw.text(
        (margin, y),
        category_name.upper(),
        font=category_font,
        fill=palette["accent"],
    )

    y += 165
    draw.text(
        (margin, y),
        '"',
        font=quote_mark_font,
        fill=palette["accent"],
    )
    y += 105

    y = _draw_wrapped(
        draw,
        tip["quote"],
        quote_font,
        margin,
        y,
        max_width,
        line_gap=24,
        fill=palette["text"],
    )

    y += 45
    draw.text(
        (margin, y),
        '"',
        font=quote_mark_font,
        fill=palette["accent"],
    )

    footer = "RELATABLE? SAVE THIS ONE."
    footer_box = draw.textbbox((0, 0), footer, font=footer_font)
    footer_width = footer_box[2] - footer_box[0]

    draw.line(
        (margin, HEIGHT - 215, WIDTH - margin, HEIGHT - 215),
        fill=palette["accent"],
        width=4,
    )
    draw.text(
        ((WIDTH - footer_width) / 2, HEIGHT - 165),
        footer,
        font=footer_font,
        fill=palette["accent"],
    )

    filename = f"{tip['id']}_pinterest.jpg"
    output_path = output_dir / filename
    image.save(output_path, format="JPEG", quality=95, optimize=True)
    return str(output_path.resolve())


def build_tip_draft(tip, category, output_dir):
    content_type = category.get("content_type", "tip")

    if content_type == "quote":
        image_path = render_quote_image(
            tip,
            category_name=category["name"],
            output_dir=output_dir,
        )
    else:
        image_path = render_tip_image(
            tip,
            category_name=category["name"],
            output_dir=output_dir,
        )

    return PinDraft(
        title=tip["title"][:100],
        description=tip["description"][:800],
        affiliate_url="",
        image_path=image_path,
        board_name=category["board"],
        topics=category.get("topics", []),
    )
