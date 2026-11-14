import re
from pathlib import Path
import requests

from models import PinDraft
from image_utils import prepare_pinterest_image


AFFILIATE_DISCLOSURE = (
    "Affiliate link — I may earn a commission from qualifying purchases."
)

HONDA_BOARD_NAME = "Vintage Honda Motorcycle Parts"
FILAMENT_BOARD_NAME = "3D Printer Filament & Materials"
BAMBU_BOARD_NAME = "Bambu Lab Parts & Accessories"
CREALITY_BOARD_NAME = "Creality 3D Printer Parts"
PRINTER_PARTS_BOARD_NAME = "3D Printer Parts & Upgrades"
PRINTER_ACCESSORIES_BOARD_NAME = "3D Printer Accessories"


HONDA_PART_LABELS = [
    (("carburetor", "carburetors", "carb "), "Carburetors"),
    (("gas tank", "fuel tank", "tank"), "Fuel Tank"),
    (("speedometer", "tachometer", "gauge", "gauges"), "Gauges"),
    (("exhaust", "muffler"), "Exhaust System"),
    (("seat",), "Seat"),
    (("cylinder head",), "Cylinder Head"),
    (("engine",), "Engine Part"),
    (("oem",), "OEM Part"),
]

PRINTER_PART_LABELS = [
    (("filament dryer", "dryer"), "Filament Dryer"),
    (("build plate", "build surface", "pei plate"), "Build Plate"),
    (("hotend", "hot end"), "Hotend"),
    (("extruder",), "Extruder"),
    (("nozzle",), "Nozzle"),
    (("motherboard", "mainboard", "controller board"), "Motherboard"),
    (("screen", "display"), "Display"),
    (("enclosure",), "Enclosure"),
    (("ams",), "AMS Accessory"),
    (("filament", "pla", "petg", "tpu", "abs", "asa"), "Filament"),
]


HONDA_TOPICS = [
    "Motorcycles",
    "Motorcycle Parts",
    "Vintage Motorcycles",
    "Motorcycle Restoration",
    "Honda Motorcycles",
]

PRINTER_TOPICS = [
    "3D Printing",
    "3D Printers",
    "3D Printer",
    "3D Printer Projects",
    "3D Printer Accessories",
]

FILAMENT_TOPICS = [
    "3D Printing",
    "3D Printers",
    "3D Printer Filament",
    "3D Printer Materials",
    "3D Printer Projects",
]


def _clean_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _combined_text(product) -> str:
    return f"{product.search_category} {product.title}".lower()


def _is_3d_printing(product) -> bool:
    text = _combined_text(product)
    return (
        "3d print" in text
        or "filament" in text
        or "bambu" in text
        or "creality" in text
        or "ender" in text
        or "cr-10" in text
    )


def _is_honda(product) -> bool:
    text = _combined_text(product)
    return "honda" in text or "cb750" in text or "cb900" in text


def _detect_label(product, labels, fallback):
    haystack = _combined_text(product)
    for keywords, label in labels:
        if any(keyword in haystack for keyword in keywords):
            return label
    return fallback


def _extract_honda_models(title: str) -> list[str]:
    models = []
    for model in re.findall(r"\bCB\d{3,4}[A-Z]?\b", (title or "").upper()):
        if model not in models:
            models.append(model)
    return models[:5]


def _extract_year_range(title: str) -> str:
    match = re.search(r"\b(\d{2,4})\s*[-–]\s*(\d{2,4})\b", title or "")
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    year = re.search(r"\b(19\d{2}|20\d{2})\b", title or "")
    return year.group(1) if year else ""


def _extract_qualifiers(title: str) -> list[str]:
    text = (title or "").lower()
    candidates = [
        ("oem", "OEM"),
        ("genuine", "Genuine"),
        ("stainless", "Stainless"),
        ("hardened steel", "Hardened Steel"),
        ("pei", "PEI"),
        ("new", "New"),
        ("nos", "NOS"),
    ]
    result = []
    for needle, label in candidates:
        if needle in text and label not in result:
            result.append(label)
    return result[:2]


def _extract_printer_brand(product) -> str:
    text = _combined_text(product)
    brands = [
        ("bambu lab", "Bambu Lab"),
        ("bambu", "Bambu Lab"),
        ("creality", "Creality"),
        ("prusa", "Prusa"),
        ("elegoo", "Elegoo"),
        ("anycubic", "Anycubic"),
        ("sunlu", "SUNLU"),
        ("overture", "Overture"),
        ("esun", "eSUN"),
        ("hatchbox", "Hatchbox"),
    ]
    for needle, label in brands:
        if needle in text:
            return label
    return ""


def _extract_printer_models(title: str) -> list[str]:
    upper = (title or "").upper()
    patterns = [
        r"\bENDER\s*3(?:\s*(?:V\d|S1|NEO))?\b",
        r"\bCR-?10(?:\s*SE)?\b",
        r"\bK1(?:C|MAX)?\b",
        r"\bX1C\b",
        r"\bX1\b",
        r"\bP1S\b",
        r"\bP1P\b",
        r"\bA1\s*MINI\b",
        r"\bA1\b",
        r"\bAMS\s*LITE\b",
        r"\bAMS\b",
    ]
    found = []
    for pattern in patterns:
        for value in re.findall(pattern, upper):
            value = _clean_spaces(value)
            if value and value not in found:
                found.append(value)
    return found[:4]


def _extract_filament_material(product) -> str:
    text = _combined_text(product)
    for token in ("PETG", "PLA", "TPU", "ASA", "ABS"):
        if re.search(rf"\b{token}\b", text, re.IGNORECASE):
            return token
    return "3D Printer"


def _truncate(text: str, max_chars=100) -> str:
    text = _clean_spaces(text)
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 1].rstrip(" |,-") + "…"


def _build_honda_title(product, max_chars=100):
    part = _detect_label(product, HONDA_PART_LABELS, "Motorcycle Part")
    models = _extract_honda_models(product.title)
    years = _extract_year_range(product.title)
    qualifiers = _extract_qualifiers(product.title)

    primary_model = "CB750"
    if models and not any(model.startswith("CB750") for model in models):
        primary_model = models[0]

    chunks = [f"Honda {primary_model} {part}"]

    if qualifiers:
        chunks.append(" ".join(qualifiers))

    if models:
        chunks.append("/".join(models))

    if years:
        chunks.append(years)

    return _truncate(" | ".join(chunks), max_chars)


def _build_3d_title(product, max_chars=100):
    part = _detect_label(product, PRINTER_PART_LABELS, "3D Printer Part")
    brand = _extract_printer_brand(product)
    models = _extract_printer_models(product.title)
    qualifiers = _extract_qualifiers(product.title)

    if part == "Filament":
        material = _extract_filament_material(product)
        primary = f"{material} Filament 1.75mm"
        if brand:
            primary += f" | {brand}"
        return _truncate(primary + " | 3D Printer Filament", max_chars)

    primary = f"{brand + ' ' if brand else ''}{part}".strip()
    if models:
        primary += f" for {'/'.join(models)}"

    chunks = [primary, "3D Printer Part"]
    if qualifiers:
        chunks.append(" ".join(qualifiers))

    return _truncate(" | ".join(chunks), max_chars)


def build_seo_title(product, max_chars=100):
    if _is_3d_printing(product):
        return _build_3d_title(product, max_chars=max_chars)
    return _build_honda_title(product, max_chars=max_chars)


def _build_honda_description(product):
    part = _detect_label(product, HONDA_PART_LABELS, "Motorcycle Part")
    models = _extract_honda_models(product.title)
    years = _extract_year_range(product.title)

    model_text = ", ".join(models) if models else "Honda CB750"
    fitment = model_text + (f" {years}" if years else "")

    sentences = [
        f"Honda CB750 {part.lower()} for {fitment}.",
        "A relevant vintage Honda motorcycle part for restoration, repair, replacement, or custom build projects.",
    ]

    if product.condition:
        sentences.append(f"Condition listed on eBay: {product.condition}.")

    sentences.append(
        "Save this Pin for your Honda CB750 parts search, then check the current eBay listing for availability and details."
    )
    sentences.append(AFFILIATE_DISCLOSURE)
    return " ".join(sentences)


def _build_3d_description(product):
    part = _detect_label(product, PRINTER_PART_LABELS, "3D Printer Part")
    brand = _extract_printer_brand(product)
    models = _extract_printer_models(product.title)

    if part == "Filament":
        material = _extract_filament_material(product)
        lead = f"{material} 1.75mm 3D printer filament"
        if brand:
            lead += f" from {brand}"
        sentences = [
            f"{lead} for FDM 3D printing.",
            "Useful for keeping filament options, colors, and materials organized for future prints and printer projects.",
        ]
    else:
        fitment = ""
        if brand:
            fitment += brand
        if models:
            fitment += (" " if fitment else "") + "/".join(models)

        lead = f"{part} for {fitment}".strip() if fitment else f"3D printer {part.lower()}"
        sentences = [
            f"{lead}.",
            "A useful 3D printer replacement part or upgrade for maintenance, repairs, and printer setup improvements.",
        ]

    if product.condition:
        sentences.append(f"Condition listed on eBay: {product.condition}.")

    sentences.append(
        "Save this Pin for your 3D printer parts and supplies search, then check the current eBay listing for compatibility, availability, and details."
    )
    sentences.append(AFFILIATE_DISCLOSURE)
    return " ".join(sentences)


def build_description(product, score_info=None, max_chars=800):
    if _is_3d_printing(product):
        text = _build_3d_description(product)
    else:
        text = _build_honda_description(product)

    return _truncate(text, max_chars=max_chars)


def build_topic_tags(product) -> list[str]:
    if _is_3d_printing(product):
        part = _detect_label(product, PRINTER_PART_LABELS, "3D Printer Part")
        topics = list(FILAMENT_TOPICS if part == "Filament" else PRINTER_TOPICS)

        brand = _extract_printer_brand(product)
        if brand == "Bambu Lab":
            topics.extend(["Bambu Lab", "Bambu Lab 3D Printer"])
        elif brand == "Creality":
            topics.extend(["Creality", "Ender 3"])

        return topics[:10]

    part = _detect_label(product, HONDA_PART_LABELS, "Motorcycle Part")
    topics = list(HONDA_TOPICS)
    if part == "Exhaust System":
        topics.append("Motorcycle Exhaust")
    elif part in ("Engine Part", "Cylinder Head"):
        topics.append("Motorcycle Engines")
    return topics[:10]


def resolve_board_name(product, default_board="", board_map=None) -> str:
    board_map = board_map or {}

    honda_board = board_map.get("honda", HONDA_BOARD_NAME)
    three_d_board = board_map.get(
        "three_d_printing",
        "3D Printer Parts, Filament & Supplies",
    )
    fallback_board = board_map.get(
        "default",
        default_board or three_d_board,
    )

    if _is_3d_printing(product):
        return three_d_board

    if _is_honda(product):
        return honda_board

    return fallback_board


def download_product_image(product, output_dir="output/pin_images"):
    if not product.image_url:
        raise RuntimeError("Selected product has no image URL.")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_id = product.legacy_item_id or "product"
    raw_path = out_dir / f"{safe_id}_raw.jpg"

    response = requests.get(product.image_url, timeout=30)
    response.raise_for_status()
    raw_path.write_bytes(response.content)

    final_path = out_dir / f"{safe_id}_pinterest.jpg"

    return prepare_pinterest_image(
        raw_path,
        output_path=final_path,
        target_width=1000,
        target_height=1500,
    )


def build_pin_draft(product, board_name="", board_map=None, score_info=None):
    image_path = download_product_image(product)

    return PinDraft(
        title=build_seo_title(product),
        description=build_description(product, score_info=score_info),
        affiliate_url=product.affiliate_url,
        image_path=image_path,
        board_name=resolve_board_name(product, board_name, board_map=board_map),
        topics=build_topic_tags(product),
    )
