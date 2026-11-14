from config import load_config
from find_best_products import collect_products
from selector import select_top_products
from pin_builder import build_pin_draft
from pinterest_browser import PinterestBrowserPublisher


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

    if not selected:
        raise RuntimeError("No eligible eBay products were found.")

    best = selected[0]
    product = best["product"]
    score_info = best["score"]

    print("\nSelected product:")
    print(product.title)
    print(f"Price: ${product.price:.2f}")
    print(f"Sold: {product.quantity_sold}")
    print(f"Score: {score_info['total']:.3f}")
    print(f"Affiliate URL: {product.affiliate_url}")

    draft = build_pin_draft(
        product=product,
        board_name=cfg["pinterest"]["board_name"],
        score_info=score_info,
    )

    print("\nPin draft prepared.")
    print(f"SEO title: {draft.title}")
    print(f"Description: {draft.description}")
    print(f"Image: {draft.image_path}")
    print(f"Board: {draft.board_name}")
    print(f"Topic tags: {', '.join(draft.topics)}")

    publisher = PinterestBrowserPublisher(cfg["pinterest"])
    publisher.publish_pin(draft)


if __name__ == "__main__":
    main()
