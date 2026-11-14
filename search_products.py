from pathlib import Path
import csv
import json
from datetime import datetime

from config import load_config, require_ebay_config
from ebay_api import EbayAPI


def passes_filters(product, cfg):
    if product.quantity_sold < int(cfg.get("minimum_quantity_sold", 0)):
        return False
    if product.price < float(cfg.get("minimum_price", 0)):
        return False
    if product.price > float(cfg.get("maximum_price", 999999)):
        return False
    if product.seller_feedback_percent < float(
        cfg.get("minimum_seller_feedback_percent", 0)
    ):
        return False
    if bool(cfg.get("require_image", True)) and not product.image_url:
        return False
    return True


def main():
    cfg = load_config()
    require_ebay_config(cfg)
    api = EbayAPI(cfg["env"])

    print("Refreshing eBay user OAuth token...")
    api.token_manager.get_user_access_token(force_refresh=True)
    print("OAuth token refreshed successfully.")

    all_products = []
    search_cfg = cfg["search"]

    for category in cfg.get("categories", []):
        if not category.get("enabled", True):
            continue

        name = category["name"]
        query = category.get("query", "").strip()
        category_id = str(category.get("category_id", "") or "").strip()

        print(f"\n=== {name} ===")
        print(f"Query: {query}")

        products = api.search(
            category_name=name,
            query=query,
            category_id=category_id,
            limit=int(search_cfg.get("results_per_category", 20)),
        )
        products = [p for p in products if passes_filters(p, search_cfg)]
        products.sort(key=lambda p: (p.quantity_sold, p.price), reverse=True)
        all_products.extend(products)

        if not products:
            print("No products passed the filters.")
            continue

        for i, p in enumerate(products[:10], 1):
            print(
                f"{i:>2}. {p.quantity_sold:>5} sold | "
                f"${p.price:>8.2f} | {p.seller_feedback_percent:>5.1f}% | "
                f"{p.title}"
            )

    output_dir = Path(cfg["env"]["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rows = [p.to_dict() for p in all_products]

    json_path = output_dir / f"ebay_products_{stamp}.json"
    csv_path = output_dir / f"ebay_products_{stamp}.csv"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    fieldnames = list(rows[0].keys()) if rows else [
        "search_category", "item_id", "legacy_item_id", "title", "price",
        "currency", "quantity_sold", "seller_username",
        "seller_feedback_percent", "image_url", "item_url",
        "affiliate_url", "ebay_category_id", "condition",
    ]

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        if rows:
            writer.writerows(rows)

    print("\nDone.")
    print(f"Products found after filtering: {len(all_products)}")
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")


if __name__ == "__main__":
    main()
