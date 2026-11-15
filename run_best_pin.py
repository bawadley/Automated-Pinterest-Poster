import argparse

from config import load_config
from find_best_products import collect_products
from history_db import PostedHistory
from selector import rank_products, select_top_products
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
        "--count",
        "--pins",
        dest="count",
        type=int,
        default=None,
        help=(
            "Number of affiliate Pins to post from the selected vertical or "
            "single category. Example: --vertical 3d --count 3. "
            "For multi-category runs, this caps the number of category winners."
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

    if args.count is not None and args.count < 1:
        raise RuntimeError("--count / --pins must be at least 1.")

    requested_count = args.count if args.count is not None else 1

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
    weights = selection_cfg.get("weights", None)

    if args.categories and len(args.categories) > 1:
        # Explicit multi-category mode: post one best fresh product from each
        # matched search category instead of choosing only one overall winner.
        ranked = rank_products(products, weights=weights)
        winners = []
        used_ids = set()

        matched_categories = []
        for product in products:
            if product.search_category not in matched_categories:
                matched_categories.append(product.search_category)

        for category_name in matched_categories:
            for row in ranked:
                product = row["product"]
                if product.search_category != category_name:
                    continue

                product_id = product.item_id or product.legacy_item_id
                if product_id in used_ids:
                    continue

                winners.append(row)
                used_ids.add(product_id)
                break

        selected = winners
        if args.count is not None:
            selected = selected[:requested_count]

        print(
            f"      Multi-category mode: selected "
            f"{len(selected)} category winner(s)."
        )
    else:
        selection_count = max(requested_count, 1)
        selected = select_top_products(
            products,
            count=selection_count,
            weights=weights,
        )
        selected = selected[:selection_count]
        print(
            f"      Requested Pins: {selection_count} | "
            f"selected {len(selected)} fresh product(s)."
        )

    if not selected:
        raise RuntimeError(
            "No fresh eligible eBay products were found. "
            "Try a larger search limit, another category, or wait for new listings."
        )

    total_to_post = len(selected)

    for post_index, best in enumerate(selected, start=1):
        product = best["product"]
        score_info = best["score"]

        print(
            f"\n=== Pin {post_index}/{total_to_post}: "
            f"{product.search_category} ==="
        )
        print("Selected product:")
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

    if total_to_post > 1:
        print(f"\nFinished multi-category run: processed {total_to_post} Pins.")


if __name__ == "__main__":
    main()
