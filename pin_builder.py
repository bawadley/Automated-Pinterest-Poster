import re
from pathlib import Path
import requests

from models import PinDraft


AFFILIATE_DISCLOSURE = (
    "Affiliate link — I may earn a commission from qualifying purchases."
)


def clean_title(title: str, max_chars=100):
    title = re.sub(r"\s+", " ", (title or "")).strip()
    if len(title) <= max_chars:
        return title
    return title[:max_chars - 1].rstrip() + "…"


def build_description(product, score_info=None, max_chars=450):
    parts = []

    parts.append(product.title.strip())

    if product.condition:
        parts.append(f"Condition: {product.condition}.")

    if product.price:
        parts.append(f"Current eBay price: ${product.price:.2f}.")

    if product.quantity_sold:
        parts.append(f"{product.quantity_sold} sold on this active listing.")

    if score_info:
        parts.append(
            "Selected by the automation based on demand, value, seller quality, "
            "and listing quality."
        )

    parts.append(AFFILIATE_DISCLOSURE)

    text = " ".join(parts)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= max_chars:
        return text

    return text[:max_chars - 1].rstrip() + "…"


def download_product_image(product, output_dir="output/pin_images"):
    if not product.image_url:
        raise RuntimeError("Selected product has no image URL.")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_id = product.legacy_item_id or "product"
    path = out_dir / f"{safe_id}.jpg"

    response = requests.get(product.image_url, timeout=30)
    response.raise_for_status()
    path.write_bytes(response.content)

    return str(path.resolve())


def build_pin_draft(product, board_name, score_info=None):
    image_path = download_product_image(product)

    return PinDraft(
        title=clean_title(product.title),
        description=build_description(product, score_info=score_info),
        affiliate_url=product.affiliate_url,
        image_path=image_path,
        board_name=board_name,
    )
