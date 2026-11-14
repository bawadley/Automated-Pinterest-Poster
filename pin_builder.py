import re
from pathlib import Path
import requests

from models import PinDraft
from image_utils import prepare_pinterest_image


AFFILIATE_DISCLOSURE = (
    "Affiliate link — I may earn a commission from qualifying purchases."
)

HONDA_BOARD_NAME = "Vintage Honda Motorcycle Parts"

PART_LABELS = [
    (("carburetor", "carburetors", "carb "), "Carburetors"),
    (("gas tank", "fuel tank", "tank"), "Fuel Tank"),
    (("speedometer", "tachometer", "gauge", "gauges"), "Gauges"),
    (("exhaust", "muffler"), "Exhaust System"),
    (("seat",), "Seat"),
    (("cylinder head",), "Cylinder Head"),
    (("engine",), "Engine Part"),
    (("oem",), "OEM Part"),
]

TOPICS_BY_PART = {
    "Carburetors": ["Motorcycles", "Motorcycle Parts", "Vintage Motorcycles", "Motorcycle Restoration", "Honda Motorcycles"],
    "Fuel Tank": ["Motorcycles", "Motorcycle Parts", "Vintage Motorcycles", "Motorcycle Restoration", "Honda Motorcycles"],
    "Gauges": ["Motorcycles", "Motorcycle Parts", "Vintage Motorcycles", "Motorcycle Restoration", "Honda Motorcycles"],
    "Exhaust System": ["Motorcycles", "Motorcycle Parts", "Motorcycle Exhaust", "Vintage Motorcycles", "Honda Motorcycles"],
    "Seat": ["Motorcycles", "Motorcycle Parts", "Vintage Motorcycles", "Motorcycle Restoration", "Honda Motorcycles"],
    "Cylinder Head": ["Motorcycles", "Motorcycle Parts", "Motorcycle Engines", "Motorcycle Restoration", "Honda Motorcycles"],
    "Engine Part": ["Motorcycles", "Motorcycle Parts", "Motorcycle Engines", "Motorcycle Restoration", "Honda Motorcycles"],
    "OEM Part": ["Motorcycles", "Motorcycle Parts", "Vintage Motorcycles", "Motorcycle Restoration", "Honda Motorcycles"],
}


def _clean_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _detect_part_label(product) -> str:
    haystack = f"{product.search_category} {product.title}".lower()
    for keywords, label in PART_LABELS:
        if any(keyword in haystack for keyword in keywords):
            return label
    return "Motorcycle Part"


def _extract_models(title: str) -> list[str]:
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
        ("aluminum", "Aluminum"),
        ("new", "New"),
        ("nos", "NOS"),
    ]
    result = []
    for needle, label in candidates:
        if needle in text and label not in result:
            result.append(label)
    return result[:2]


def build_seo_title(product, max_chars=100):
    """
    Put the primary search phrase first because Pinterest may only show
    roughly the first 40 characters in feeds.
    """
    part = _detect_part_label(product)
    models = _extract_models(product.title)
    years = _extract_year_range(product.title)
    qualifiers = _extract_qualifiers(product.title)

    primary_model = "CB750"
    for model in models:
        if model.startswith("CB750"):
            primary_model = "CB750"
            break
    else:
        if models:
            primary_model = models[0]

    chunks = [f"Honda {primary_model} {part}"]

    if qualifiers:
        chunks.append(" ".join(qualifiers))

    if models:
        compact_models = "/".join(models)
        chunks.append(compact_models)

    if years:
        chunks.append(years)

    title = " | ".join(chunks)
    title = _clean_spaces(title)

    if len(title) <= max_chars:
        return title

    return title[:max_chars - 1].rstrip(" |,-") + "…"


def build_description(product, score_info=None, max_chars=800):
    part = _detect_part_label(product)
    models = _extract_models(product.title)
    years = _extract_year_range(product.title)

    model_text = ", ".join(models) if models else "Honda CB750"
    fitment = model_text
    if years:
        fitment += f" {years}"

    sentences = [
        f"Honda CB750 {part.lower()} for {fitment}.",
        (
            f"A relevant vintage Honda motorcycle part for restoration, repair, "
            f"replacement, or custom build projects."
        ),
    ]

    if product.condition:
        sentences.append(f"Condition listed on eBay: {product.condition}.")

    sentences.append(
        "Save this Pin for your Honda CB750 parts search, then check the current "
        "eBay listing for availability and details."
    )
    sentences.append(AFFILIATE_DISCLOSURE)

    text = _clean_spaces(" ".join(sentences))

    if len(text) <= max_chars:
        return text

    return text[:max_chars - 1].rstrip() + "…"


def build_topic_tags(product) -> list[str]:
    part = _detect_part_label(product)
    topics = list(TOPICS_BY_PART.get(part, [
        "Motorcycles",
        "Motorcycle Parts",
        "Vintage Motorcycles",
        "Motorcycle Restoration",
        "Honda Motorcycles",
    ]))

    # Pinterest supports up to 10 related topics. Keep these broad and tightly
    # relevant; the UI will only select topics Pinterest actually offers.
    return topics[:10]


def resolve_board_name(product, default_board="") -> str:
    haystack = f"{product.search_category} {product.title}".lower()
    if "honda" in haystack or "cb750" in haystack or "cb900" in haystack:
        return HONDA_BOARD_NAME
    return default_board or HONDA_BOARD_NAME


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


def build_pin_draft(product, board_name="", score_info=None):
    image_path = download_product_image(product)

    return PinDraft(
        title=build_seo_title(product),
        description=build_description(product, score_info=score_info),
        affiliate_url=product.affiliate_url,
        image_path=image_path,
        board_name=resolve_board_name(product, board_name),
        topics=build_topic_tags(product),
    )
