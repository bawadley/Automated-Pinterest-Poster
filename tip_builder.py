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


QUESTION_PALETTES = [
    {
        "background": "#FFF0C9",
        "panel": "#FFF8E8",
        "text": "#2B2418",
        "accent": "#D97706",
    },
    {
        "background": "#DDF4FF",
        "panel": "#F5FBFF",
        "text": "#15334A",
        "accent": "#247BA0",
    },
    {
        "background": "#E3F4E8",
        "panel": "#F5FCF7",
        "text": "#173A26",
        "accent": "#3D8B5F",
    },
    {
        "background": "#F4E2FF",
        "panel": "#FCF6FF",
        "text": "#3D2450",
        "accent": "#8B5FBF",
    },
    {
        "background": "#FFE2E2",
        "panel": "#FFF7F7",
        "text": "#4A2020",
        "accent": "#C95A5A",
    },
]


QUIZ_PALETTES = [
    {
        "background": "#E8F0FF",
        "panel": "#F7FAFF",
        "text": "#1B2A41",
        "accent": "#3A6EA5",
    },
    {
        "background": "#FFF0D9",
        "panel": "#FFF9F0",
        "text": "#3A2A1D",
        "accent": "#D47A1F",
    },
    {
        "background": "#E8F7EA",
        "panel": "#F7FCF8",
        "text": "#1E3825",
        "accent": "#4A8F5D",
    },
    {
        "background": "#F5E8FF",
        "panel": "#FCF8FF",
        "text": "#382348",
        "accent": "#8A5FB5",
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


def render_question_image(tip, category_name, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    palette = _pick_palette(tip["id"], QUESTION_PALETTES)
    image = Image.new("RGB", (WIDTH, HEIGHT), palette["background"])
    draw = ImageDraw.Draw(image)

    category_font = _font(30, bold=True)
    prompt_font = _font(70, bold=True)
    subtext_font = _font(38)
    cta_font = _font(30, bold=True)

    margin = 95
    max_width = WIDTH - (margin * 2)

    draw.rounded_rectangle(
        (50, 50, WIDTH - 50, HEIGHT - 50),
        radius=44,
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

    y += 135
    draw.ellipse(
        (margin, y, margin + 105, y + 105),
        fill=palette["accent"],
    )
    q_font = _font(72, bold=True)
    q_box = draw.textbbox((0, 0), "?", font=q_font)
    q_w = q_box[2] - q_box[0]
    q_h = q_box[3] - q_box[1]
    draw.text(
        (margin + (105 - q_w) / 2, y + (105 - q_h) / 2 - 8),
        "?",
        font=q_font,
        fill=palette["panel"],
    )

    y += 155
    y = _draw_wrapped(
        draw,
        tip["prompt"],
        prompt_font,
        margin,
        y,
        max_width,
        line_gap=24,
        fill=palette["text"],
    )

    y += 55
    draw.line(
        (margin, y, WIDTH - margin, y),
        fill=palette["accent"],
        width=4,
    )
    y += 50

    y = _draw_wrapped(
        draw,
        tip.get("subtext", ""),
        subtext_font,
        margin,
        y,
        max_width,
        line_gap=16,
        fill=palette["text"],
    )

    cta = tip.get("cta", "JOIN THE CONVERSATION")
    cta_box = draw.textbbox((0, 0), cta, font=cta_font)
    cta_width = cta_box[2] - cta_box[0]

    draw.rounded_rectangle(
        (
            (WIDTH - cta_width) / 2 - 30,
            HEIGHT - 190,
            (WIDTH + cta_width) / 2 + 30,
            HEIGHT - 105,
        ),
        radius=24,
        fill=palette["accent"],
    )
    draw.text(
        ((WIDTH - cta_width) / 2, HEIGHT - 165),
        cta,
        font=cta_font,
        fill=palette["panel"],
    )

    filename = f"{tip['id']}_pinterest.jpg"
    output_path = output_dir / filename
    image.save(output_path, format="JPEG", quality=95, optimize=True)
    return str(output_path.resolve())


def render_quiz_image(tip, category_name, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    palette = _pick_palette(tip["id"], QUIZ_PALETTES)
    image = Image.new("RGB", (WIDTH, HEIGHT), palette["background"])
    draw = ImageDraw.Draw(image)

    category_font = _font(30, bold=True)
    prompt_font = _font(62, bold=True)
    option_font = _font(40, bold=True)
    cta_font = _font(30, bold=True)

    margin = 90
    max_width = WIDTH - (margin * 2)

    draw.rounded_rectangle(
        (50, 50, WIDTH - 50, HEIGHT - 50),
        radius=44,
        fill=palette["panel"],
        outline=palette["accent"],
        width=8,
    )

    y = 105
    draw.text(
        (margin, y),
        category_name.upper(),
        font=category_font,
        fill=palette["accent"],
    )

    y += 105
    draw.text(
        (margin, y),
        "QUICK QUIZ",
        font=_font(40, bold=True),
        fill=palette["accent"],
    )

    y += 85
    y = _draw_wrapped(
        draw,
        tip["prompt"],
        prompt_font,
        margin,
        y,
        max_width,
        line_gap=20,
        fill=palette["text"],
    )

    y += 45

    for option in tip.get("options", []):
        option_lines = _wrap_for_width(draw, option, option_font, max_width - 60)
        option_height = max(105, len(option_lines) * 52 + 45)

        draw.rounded_rectangle(
            (margin, y, WIDTH - margin, y + option_height),
            radius=24,
            outline=palette["accent"],
            width=4,
        )

        option_y = y + 22
        for line in option_lines:
            draw.text(
                (margin + 30, option_y),
                line,
                font=option_font,
                fill=palette["text"],
            )
            option_y += 52

        y += option_height + 28

    cta = tip.get("cta", "COMMENT YOUR ANSWER")
    cta_box = draw.textbbox((0, 0), cta, font=cta_font)
    cta_width = cta_box[2] - cta_box[0]

    draw.rounded_rectangle(
        (
            (WIDTH - cta_width) / 2 - 30,
            HEIGHT - 185,
            (WIDTH + cta_width) / 2 + 30,
            HEIGHT - 105,
        ),
        radius=24,
        fill=palette["accent"],
    )
    draw.text(
        ((WIDTH - cta_width) / 2, HEIGHT - 161),
        cta,
        font=cta_font,
        fill=palette["panel"],
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
    elif content_type == "question":
        image_path = render_question_image(
            tip,
            category_name=category["name"],
            output_dir=output_dir,
        )
    elif content_type == "quiz":
        image_path = render_quiz_image(
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
