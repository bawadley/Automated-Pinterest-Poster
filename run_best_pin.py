import argparse

from config import load_config
from find_best_products import collect_products
from selector import select_top_products
from pin_builder import build_pin_draft
from pinterest_browser import PinterestBrowserPublisher


def parse_args():
    parser = argparse.ArgumentParser(
        description="Find and prepare the best eBay product for Pinterest."
    )
    parser.add_argument(
        "--category",
        help=(
            "Search only categories whose name/query contains this text. "
            "Example: --category \"PLA Filament\""
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
    if args.category:
        print(f"Filter: category contains = {args.category}")

    products = collect_products(
        cfg,
        category_filter=args.category,
        vertical=args.vertical,
    )

    print("\n[4/4] Ranking eligible products...")
    selection_cfg = cfg.get("selection", {})
    top_count = int(selection_cfg.get("top_count", 5))
    weights = selection_cfg.get("weights", None)

    selected = select_top_products(
        products,
        count=top_count,
        weights=weights,
    )

    if not selected:
        raise RuntimeError("No eligible eBay products were found.")

    best = selected[0]
    product = best["product"]
    score_info = best["score"]

    print("      Best product selected.")
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
    publisher.publish_pin(draft)


if __name__ == "__main__":
    main()
