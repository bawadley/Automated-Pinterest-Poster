import argparse

from config import load_config
from find_best_products import collect_products
from history_db import PostedHistory
from selector import select_top_products
from pin_builder import build_pin_draft
from pinterest_browser import PinterestBrowserPublisher


def parse_args():
    parser = argparse.ArgumentParser(
        description="Find and prepare the best eBay product for Pinterest."
    )
    parser.add_argument(
        "--category",
        action="append",
        dest="categories",
        help=(
            "Search only categories whose name/query contains this text. "
            "Repeat --category to search multiple categories in one run. "
            "Example: --category \"PLA Filament\" --category \"Bambu Lab Parts\""
        ),
    )
    parser.add_argument(
        "--vertical",
        choices=["honda", "3d"],
        help=(
            "Search only one vertical. Use 'honda' for CB750/Honda parts "
            "or '3d' for 3D-printing products."
        ),
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List enabled search categories and exit without calling eBay.",
    )
    return parser.parse_args()


def print_categories(cfg):
    print("\nEnabled search categories:\n")
    for category in cfg.get("categories", []):
        if category.get("enabled", True):
            print(f"- {category['name']}")


def main():
    args = parse_args()
    cfg = load_config()

    print("\n=== eBay -> Pinterest Automation ===")

    if args.list_categories:
        print_categories(cfg)
        return

    if args.vertical:
        print(f"Filter: vertical = {args.vertical}")
    if args.categories:
        print(
            "Filter: categories contain = "
            + ", ".join(args.categories)
        )

    selection_cfg = cfg.get("selection", {})
    cooldown_days = int(selection_cfg.get("cooldown_days", 90))
    history_path = selection_cfg.get(
        "history_db_path",
        "data/posted_history.db",
    )

    history = PostedHistory(history_path)
    excluded_ids = history.recent_item_ids(cooldown_days)

    print(
        f"Posted-history database: {history_path} "
        f"({history.posted_count()} total saved)"
    )
    print(
        f"Cooldown: {cooldown_days} days | "
        f"{len(excluded_ids)} recent item ID(s) excluded"
    )

    products = collect_products(
        cfg,
        category_filter=args.categories,
        vertical=args.vertical,
        excluded_ids=excluded_ids,
    )

    print("\n[4/4] Ranking eligible products...")
    top_count = int(selection_cfg.get("top_count", 5))
    weights = selection_cfg.get("weights", None)

    selected = select_top_products(
        products,
        count=top_count,
        weights=weights,
    )

    if not selected:
        raise RuntimeError(
            "No fresh eligible eBay products were found. "
            "Try a larger search limit, another category, or wait for new listings."
        )

    best = selected[0]
    product = best["product"]
    score_info = best["score"]

    print("      Best fresh product selected.")
    print("\nSelected product:")
    print(product.title)
    print(f"Price: ${product.price:.2f}")
    print(f"Sold: {product.quantity_sold}")
    print(f"Score: {score_info['total']:.3f}")
    print(f"Affiliate URL: {product.affiliate_url}")

    print("\nPreparing Pinterest image, SEO copy, board, and topic tags...")
    draft = build_pin_draft(
        product=product,
        board_name=cfg["pinterest"]["board_name"],
        board_map=cfg.get("pinterest_boards", {}),
        score_info=score_info,
    )

    print("Pinterest draft ready.")
    print(f"SEO title: {draft.title}")
    print(f"Description: {draft.description}")
    print(f"Image: {draft.image_path}")
    print(f"Board: {draft.board_name}")
    print(f"Topic tags: {', '.join(draft.topics)}")

    print("\nOpening Pinterest browser and populating the Pin form...")
    publisher = PinterestBrowserPublisher(cfg["pinterest"])
    published = publisher.publish_pin(draft)

    if published:
        history.mark_posted(product, score=score_info)
        print(
            f"Saved eBay item {product.legacy_item_id or product.item_id} "
            f"to posted history."
        )
        print(
            f"It will be excluded from selection for the next "
            f"{cooldown_days} days."
        )
    else:
        print(
            "Dry run / no confirmed publish: item was NOT added to posted history."
        )


if __name__ == "__main__":
    main()
