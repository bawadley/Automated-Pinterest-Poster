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



# Layout engine v2: each card gets one of four compositions chosen from its
# content ID. The palette is selected independently, multiplying visual variety.
def _layout_index(item_id):
    digest = hashlib.sha256(("layout:" + str(item_id)).encode("utf-8")).digest()
    return digest[0] % 4


def _fit_block(draw, value, width, height, max_size=70, min_size=23, bold=True,
               gap=12):
    value = str(value or "").strip()
    for size in range(max_size, min_size - 1, -2):
        font = _font(size, bold=bold)
        lines = _wrap_for_width(draw, value, font, width)
        line_height = draw.textbbox((0, 0), "Ag", font=font)[3] + gap
        if len(lines) * line_height <= height:
            return font, lines, line_height
    font = _font(min_size, bold=bold)
    lines = _wrap_for_width(draw, value, font, width)
    line_height = draw.textbbox((0, 0), "Ag", font=font)[3] + gap
    return font, lines, line_height


def _block(draw, value, x, y, width, height, color, size=70, min_size=23,
           bold=True, center=False, gap=12):
    font, lines, line_height = _fit_block(
        draw, value, width, height, size, min_size, bold, gap
    )
    # If unusually long AI text remains, keep the artwork inside its box.
    visible_lines = max(1, int(height // line_height))
    for line in lines[:visible_lines]:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        tx = x + (width - line_width) / 2 if center else x
        draw.text((tx, y), line, font=font, fill=color)
        y += line_height
    return y


def _chip(draw, text, xy, bg, fg, max_width=780):
    x, y = xy
    size = 26
    font = _font(size, bold=True)
    label = str(text).upper()
    while size > 17 and draw.textbbox((0, 0), label, font=font)[2] > max_width:
        size -= 2
        font = _font(size, bold=True)
    bbox = draw.textbbox((0, 0), label, font=font)
    width = min(max_width, bbox[2] + 48)
    draw.rounded_rectangle((x, y, x + width, y + 56), radius=22, fill=bg)
    draw.text((x + 24, y + 12), label, fill=fg, font=font)


def _save_varied(image, tip, output_dir):
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{tip['id']}_pinterest.jpg"
    image.save(path, format="JPEG", quality=95, optimize=True)
    return str(path.resolve())


def render_varied_image(tip, category_name, output_dir, content_type):
    palettes = {
        "tip": TIP_PALETTES,
        "quote": QUOTE_PALETTES,
        "question": QUESTION_PALETTES,
        "quiz": QUIZ_PALETTES,
    }
    palette = _pick_palette(tip["id"], palettes.get(content_type, TIP_PALETTES))
    layout = _layout_index(tip["id"])
    bg, panel = palette["background"], palette["panel"]
    ink, accent = palette["text"], palette["accent"]

    image = Image.new("RGB", (WIDTH, HEIGHT), bg)
    d = ImageDraw.Draw(image)

    # Four distinct visual systems: editorial, bold headline, split panels,
    # and floating card. Keep substantial safe margins for Pinterest crops.
    if layout == 0:
        d.rectangle((0, 0, WIDTH, 190), fill=accent)
        d.rounded_rectangle((52, 220, 948, 1435), radius=30, fill=panel)
        _chip(d, category_name, (88, 77), panel, ink, 770)
        title_box = (100, 280, 800, 410)
        content_box = (100, 760, 800, 520)
        footer_y = 1345
        _block(d, "01 / FIELD NOTES", 102, 227, 700, 48, accent, 30, 23)
    elif layout == 1:
        d.rectangle((0, 0, WIDTH, 730), fill=accent)
        d.rounded_rectangle((58, 670, 942, 1420), radius=48, fill=panel)
        d.ellipse((770, 110, 1120, 460), outline=panel, width=14)
        d.ellipse((805, 140, 1090, 425), outline=panel, width=4)
        _chip(d, category_name, (80, 70), panel, ink, 790)
        title_box = (88, 230, 825, 400)
        content_box = (110, 765, 780, 500)
        footer_y = 1345
    elif layout == 2:
        d.polygon([(0, 0), (1000, 0), (1000, 315), (0, 560)], fill=accent)
        d.rounded_rectangle((60, 580, 940, 1425), radius=28, fill=panel)
        d.rectangle((60, 580, 86, 1425), fill=accent)
        _chip(d, category_name, (75, 85), panel, ink, 780)
        title_box = (100, 265, 790, 270)
        content_box = (118, 655, 760, 610)
        footer_y = 1348
    else:
        d.rounded_rectangle((45, 45, 955, 1455), radius=52,
                            outline=accent, width=9)
        d.rectangle((80, 80, 920, 205), fill=accent)
        d.rounded_rectangle((80, 625, 920, 1340), radius=38, fill=panel)
        d.line((120, 575, 880, 575), fill=accent, width=8)
        _chip(d, category_name, (105, 111), panel, ink, 760)
        title_box = (112, 260, 770, 300)
        content_box = (125, 705, 750, 535)
        footer_y = 1380

    tx, ty, tw, th = title_box
    cx, cy, cw, ch = content_box
    title_color = panel if layout in (1, 2) else ink

    if content_type == "tip":
        headline = tip.get("headline", "")
        _block(d, headline, tx, ty, tw, th, title_color, size=75, min_size=29)
        body = tip.get("body", "")
        bullets = tip.get("bullets", [])[:3]
        body_height = min(230, int(ch * 0.46))
        next_y = _block(d, body, cx, cy, cw, body_height, ink,
                        size=36, min_size=23, bold=False)
        bullet_top = max(cy + body_height + 20, next_y + 24)
        remaining = max(75, cy + ch - bullet_top)
        per_bullet = remaining / max(len(bullets), 1)
        for i, bullet in enumerate(bullets):
            by = bullet_top + i * per_bullet
            d.ellipse((cx, by + 12, cx + 14, by + 26), fill=accent)
            _block(d, bullet, cx + 30, by, cw - 30, per_bullet - 6, ink,
                   size=29, min_size=20, bold=False, gap=5)
        footer = "SAVE FOR LATER"
    elif content_type == "quote":
        d.text((tx, ty - 30), "“", font=_font(120, True), fill=title_color)
        _block(d, tip.get("quote", ""), tx, ty + 135, tw,
               th + ch - 65, title_color if layout in (1, 2) else ink,
               size=70, min_size=31)
        if layout == 1:
            _block(d, "A LITTLE RELATABLE HUMOR", cx, cy + 250, cw, 80, ink,
                   size=27)
        footer = "RELATABLE? SAVE IT"
    elif content_type == "question":
        _block(d, "LET'S TALK", tx, ty, tw, 65, title_color, size=32)
        _block(d, tip.get("prompt", ""), tx, ty + 100, tw, th - 105,
               title_color, size=75, min_size=29)
        d.ellipse((cx, cy + 10, cx + 90, cy + 100), fill=accent)
        _block(d, "?", cx + 16, cy + 10, 60, 83, panel, size=60, center=True)
        _block(d, tip.get("subtext", ""), cx, cy + 140, cw, ch - 185,
               ink, size=39, min_size=24, bold=False)
        footer = tip.get("cta") or "JOIN THE CONVERSATION"
    else:
        _block(d, "QUICK QUIZ", tx, ty, tw, 65, title_color, size=34)
        _block(d, tip.get("prompt", ""), tx, ty + 100, tw, th - 110,
               title_color, size=61, min_size=28)
        options = tip.get("options", [])[:3]
        option_height = min(148, (ch - 20) / max(len(options), 1) - 12)
        for i, option in enumerate(options):
            oy = cy + 10 + i * (option_height + 15)
            if layout % 2:
                d.rounded_rectangle(
                    (cx, oy, cx + cw, oy + option_height),
                    radius=18, outline=accent, width=4
                )
            else:
                d.rounded_rectangle(
                    (cx, oy, cx + cw, oy + option_height),
                    radius=18, fill=bg
                )
            _block(d, option, cx + 24, oy + 17, cw - 48,
                   option_height - 23, ink, size=36, min_size=22)
        footer = tip.get("cta") or "COMMENT YOUR ANSWER"

    # Footer treatment changes with the composition.
    footer_size = 25
    footer_font = _font(footer_size, bold=True)
    while footer_size > 17 and d.textbbox((0, 0), footer.upper(),
                                          font=footer_font)[2] > 740:
        footer_size -= 2
        footer_font = _font(footer_size, bold=True)
    footer_width = d.textbbox((0, 0), footer.upper(), font=footer_font)[2]
    footer_x = (WIDTH - footer_width) / 2
    if layout in (0, 2):
        d.line((140, footer_y - 25, 860, footer_y - 25), fill=accent, width=4)
        d.text((footer_x, footer_y), footer.upper(), font=footer_font,
               fill=accent)
    elif layout == 1:
        d.rounded_rectangle((165, footer_y - 20, 835, footer_y + 55),
                            radius=22, fill=accent)
        d.text((footer_x, footer_y), footer.upper(), font=footer_font,
               fill=panel)
    else:
        d.text((footer_x, footer_y), footer.upper(), font=footer_font,
               fill=accent)
    return _save_varied(image, tip, output_dir)


def build_tip_draft(tip, category, output_dir):
    content_type = category.get("content_type", "tip")

    image_path = render_varied_image(
        tip,
        category_name=category["name"],
        output_dir=output_dir,
        content_type=content_type,
    )

    return PinDraft(
        title=tip["title"][:100],
        description=tip["description"][:800],
        affiliate_url="",
        image_path=image_path,
        board_name=category["board"],
        topics=category.get("topics", []),
    )
