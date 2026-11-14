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


def _draw_wrapped(draw, text, font, x, y, max_width, line_gap=14):
    lines = _wrap_for_width(draw, text, font, max_width)
    line_height = draw.textbbox((0, 0), "Ag", font=font)[3]
    for line in lines:
        draw.text((x, y), line, font=font, fill="black")
        y += line_height + line_gap
    return y


def render_tip_image(tip, category_name, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
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
        radius=34,
        outline="black",
        width=4,
    )

    y = 110
    draw.text((margin, y), category_name.upper(), font=category_font, fill="black")
    y += 85

    y = _draw_wrapped(
        draw,
        tip["headline"],
        title_font,
        margin,
        y,
        max_width,
        line_gap=20,
    )

    y += 55
    draw.line((margin, y, WIDTH - margin, y), fill="black", width=3)
    y += 55

    y = _draw_wrapped(
        draw,
        tip["body"],
        body_font,
        margin,
        y,
        max_width,
        line_gap=16,
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
        )
        y += 18

    footer = "SAVE THIS TIP FOR LATER"
    footer_box = draw.textbbox((0, 0), footer, font=footer_font)
    footer_width = footer_box[2] - footer_box[0]
    draw.text(
        ((WIDTH - footer_width) / 2, HEIGHT - 150),
        footer,
        font=footer_font,
        fill="black",
    )

    filename = f"{tip['id']}_pinterest.jpg"
    output_path = output_dir / filename
    image.save(output_path, format="JPEG", quality=95, optimize=True)
    return str(output_path.resolve())


def render_quote_image(tip, category_name, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)

    category_font = _font(32, bold=True)
    quote_font = _font(64, bold=True)
    footer_font = _font(28, bold=True)

    margin = 105
    max_width = WIDTH - (margin * 2)

    draw.rounded_rectangle(
        (55, 55, WIDTH - 55, HEIGHT - 55),
        radius=34,
        outline="black",
        width=4,
    )

    y = 120
    draw.text(
        (margin, y),
        category_name.upper(),
        font=category_font,
        fill="black",
    )

    y += 170
    draw.text((margin, y), '"', font=_font(110, bold=True), fill="black")
    y += 110

    y = _draw_wrapped(
        draw,
        tip["quote"],
        quote_font,
        margin,
        y,
        max_width,
        line_gap=24,
    )

    y += 50
    draw.text((margin, y), '"', font=_font(110, bold=True), fill="black")

    footer = "RELATABLE? SAVE THIS ONE."
    footer_box = draw.textbbox((0, 0), footer, font=footer_font)
    footer_width = footer_box[2] - footer_box[0]
    draw.text(
        ((WIDTH - footer_width) / 2, HEIGHT - 150),
        footer,
        font=footer_font,
        fill="black",
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
