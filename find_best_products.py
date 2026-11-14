from config import load_config, require_ebay_config
from ebay_api import EbayAPI
from selector import select_top_products


def passes_filters(product, cfg):
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

    # Intentionally allow zero-sold listings. High-value one-off parts can
    # still be good affiliate opportunities.
    return True


def _matches_vertical(category, vertical):
    if not vertical:
        return True

    text = f"{category.get('name', '')} {category.get('query', '')}".lower()
    vertical = vertical.strip().lower()

    aliases = {
        "honda": ("honda", "cb750", "cb900"),
        "motorcycle": ("honda", "cb750", "cb900"),
        "3d": ("3d printing", "3d printer", "filament", "bambu", "creality", "ender", "cr-10"),
        "3d-printing": ("3d printing", "3d printer", "filament", "bambu", "creality", "ender", "cr-10"),
        "printer": ("3d printing", "3d printer", "filament", "bambu", "creality", "ender", "cr-10"),
    }

    keywords = aliases.get(vertical, (vertical,))
    return any(keyword in text for keyword in keywords)


def _matches_category(category, category_filter):
    if not category_filter:
        return True

    needle = category_filter.strip().lower()
    name = category.get("name", "").lower()
    query = category.get("query", "").lower()

    return needle in name or needle in query


def _progress_bar(current, total, width=28):
    if total <= 0:
        return "[" + ("-" * width) + "]"

    ratio = min(max(current / total, 0.0), 1.0)
    filled = int(width * ratio)
    return "[" + ("#" * filled) + ("-" * (width - filled)) + "]"


def collect_products(cfg, category_filter=None, vertical=None):
    require_ebay_config(cfg)
    api = EbayAPI(cfg["env"])
    search_cfg = cfg["search"]

    print("[1/4] Refreshing eBay OAuth token...")
    api.token_manager.get_user_access_token(force_refresh=True)
    print("      OAuth token ready.")

    categories = []
    for category in cfg.get("categories", []):
        if not category.get("enabled", True):
            continue
        if not _matches_vertical(category, vertical):
            continue
        if not _matches_category(category, category_filter):
            continue
        categories.append(category)

    if (category_filter or vertical) and not categories:
        filters = []
        if vertical:
            filters.append(f"vertical={vertical!r}")
        if category_filter:
            filters.append(f"category={category_filter!r}")
        raise RuntimeError(
            "No enabled categories matched " + ", ".join(filters) + "."
        )

    products = []
    total_categories = len(categories)

    print(f"[2/4] Searching {total_categories} categor{'y' if total_categories == 1 else 'ies'}...")

    for category_index, category in enumerate(categories, start=1):
        category_limit = int(
            category.get(
                "results_per_category",
                search_cfg.get("results_per_category", 20),
            )
        )

        print(
            f"\n  Category {category_index}/{total_categories}: "
            f"{category['name']}"
        )
        print(f"  Query: {category.get('query', '')}")
        print(f"  Requested listings: {category_limit}")

        def on_progress(current, total, message):
            bar = _progress_bar(current, total)
            percent = int((current / total) * 100) if total else 0
            print(
                f"\r  {bar} {percent:3d}%  {message}",
                end="",
                flush=True,
            )

        results = api.search(
            category_name=category["name"],
            query=category.get("query", ""),
            category_id=str(category.get("category_id", "") or ""),
            limit=category_limit,
            progress_callback=on_progress,
        )
        print()

        passed = [
            p for p in results
            if passes_filters(p, search_cfg)
        ]
        products.extend(passed)

        print(
            f"  Finished {category['name']}: "
            f"{len(passed)}/{len(results)} listings passed filters."
        )

    print(
        f"\n[3/4] Search complete. "
        f"{len(products)} eligible listings collected."
    )

    return products


def main():
    cfg = load_config()
    products = collect_products(cfg)

    selection_cfg = cfg.get("selection", {})
    top_count = int(selection_cfg.get("top_count", 5))
    weights = selection_cfg.get("weights", None)

    selected = select_top_products(
        products,
        count=top_count,
        weights=weights,
    )

    print(f"\nTop {len(selected)} diverse products to promote:\n")

    for i, row in enumerate(selected, 1):
        p = row["product"]
        s = row["score"]

        print(
            f"{i}. score={s['total']:.3f} | "
            f"{p.quantity_sold} sold | "
            f"${p.price:.2f} | "
            f"{p.search_category} | "
            f"{p.title}"
        )

        print(
            f"   demand={s['demand']:.2f} "
            f"value={s['value']:.2f} "
            f"category={s['category_value']:.2f} "
            f"seller={s['seller']:.2f} "
            f"quality={s['listing_quality']:.2f}"
        )


if __name__ == "__main__":
    main()
