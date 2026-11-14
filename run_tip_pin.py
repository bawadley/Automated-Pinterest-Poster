import argparse

from ai_content_generator import AIContentGenerator
from config import load_config
from pinterest_browser import PinterestBrowserPublisher
from tip_builder import build_tip_draft, load_tip_config
from tip_history import TipHistory


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create and publish non-affiliate Pinterest tip Pins."
    )
    parser.add_argument(
        "--category",
        action="append",
        dest="categories",
        help=(
            "Tip category filter. Repeat to test multiple categories. "
            "Example: --category \"PETG Tips\" --category \"First Layer Tips\""
        ),
    )
    parser.add_argument(
        "--vertical",
        choices=["3d", "honda"],
        help="Limit non-affiliate categories to one vertical.",
    )
    parser.add_argument(
        "--content-type",
        choices=["tip", "quote", "question", "quiz", "all"],
        default="all",
        help=(
            "Choose which non-affiliate content to run: "
            "'tip', 'quote', 'question', 'quiz', or 'all'."
        ),
    )
    parser.add_argument(
        "--static",
        action="store_true",
        help=(
            "Use the prewritten tip_config.yaml content instead of AI "
            "generation for this run."
        ),
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available tip categories and exit.",
    )
    return parser.parse_args()


def _matches(category, filters, vertical, content_type):
    if vertical and category.get("vertical") != vertical:
        return False

    category_type = category.get("content_type", "tip")
    if content_type != "all" and category_type != content_type:
        return False

    if not filters:
        return True

    name = category.get("name", "").lower()
    return any(str(value).strip().lower() in name for value in filters)


def _pick_fresh_tip(category, excluded_ids):
    for tip in category.get("tips", []):
        if tip.get("id") not in excluded_ids:
            return tip
    return None


def main():
    args = parse_args()
    app_cfg = load_config()
    tip_cfg = load_tip_config()

    categories = [
        category
        for category in tip_cfg.get("tip_categories", [])
        if _matches(
            category,
            args.categories,
            args.vertical,
            args.content_type,
        )
    ]

    if args.list_categories:
        print("\nAvailable non-affiliate categories:\n")
        for category in tip_cfg.get("tip_categories", []):
            content_type = category.get("content_type", "tip")
            print(
                f"- {category['name']} "
                f"[{category.get('vertical', '')} | {content_type}]"
            )
        return

    if not categories:
        raise RuntimeError("No tip categories matched your filters.")

    settings = tip_cfg.get("tip_settings", {})
    history = TipHistory(
        settings.get("history_db_path", "data/tip_history.db")
    )
    cooldown_days = int(settings.get("cooldown_days", 365))
    excluded_ids = history.recent_tip_ids(cooldown_days)
    output_dir = settings.get("output_dir", "output/tip_images")

    print("\n=== Pinterest Non-Affiliate Content Automation ===")
    print(f"Content type: {args.content_type}")
    if args.categories:
        print("Tip categories: " + ", ".join(args.categories))
    if args.vertical:
        print(f"Vertical: {args.vertical}")
    print(
        f"Tip history: {history.posted_count()} saved | "
        f"{len(excluded_ids)} excluded for {cooldown_days} days"
    )

    ai_generator = AIContentGenerator(app_cfg.get("ai", {}))
    ai_enabled = ai_generator.available and not args.static

    if args.static:
        print("Content source: static tip_config.yaml (--static)")
    elif ai_enabled:
        print(
            f"Content source: AI generation "
            f"({app_cfg['ai'].get('model', 'gpt-6-luna')})"
        )
    else:
        print(
            "Content source: static fallback "
            "(OPENAI_API_KEY is not configured)"
        )

    # Explicit multiple-category filters intentionally produce one fresh Pin
    # per matched category, mirroring the affiliate multi-category test mode.
    if args.categories:
        categories_to_post = categories
    else:
        categories_to_post = categories[:1]

    publisher = PinterestBrowserPublisher(app_cfg["pinterest"])
    processed = 0

    for index, category in enumerate(categories_to_post, start=1):
        tip = None
        generated_by_ai = False

        if ai_enabled:
            previous_items = history.posted_items(limit=100)
            try:
                print(
                    f"\nGenerating fresh AI "
                    f"{category.get('content_type', 'tip')}..."
                )
                tip = ai_generator.generate(
                    category,
                    previous_items=previous_items,
                )
                generated_by_ai = True
                print("AI content generated and passed duplicate checks.")
            except Exception as exc:
                print(
                    f"WARNING: AI generation failed: {exc}"
                )
                print(
                    "Falling back to the prewritten content library "
                    "for this Pin."
                )

        if tip is None:
            tip = _pick_fresh_tip(category, excluded_ids)

        if not tip:
            print(
                f"\nNo unused static content remains in category: "
                f"{category['name']}"
            )
            continue

        print(
            f"\n=== Tip {index}/{len(categories_to_post)}: "
            f"{category['name']} ==="
        )
        print(f"Tip ID: {tip['id']}")
        print(f"Title: {tip['title']}")
        content_type = category.get("content_type", "tip")
        if content_type == "quote":
            print(f"Quote: {tip['quote']}")
        elif content_type == "question":
            print(f"Prompt: {tip['prompt']}")
        elif content_type == "quiz":
            print(f"Quiz: {tip['prompt']}")
            print("Choices: " + " | ".join(tip.get("options", [])))
        else:
            print(f"Headline: {tip['headline']}")

        draft = build_tip_draft(
            tip,
            category,
            output_dir=output_dir,
        )

        print(f"Image: {draft.image_path}")
        print(f"Board: {draft.board_name}")
        print(f"Topic tags: {', '.join(draft.topics)}")
        print("Destination link: none (non-affiliate Pin)")

        published = publisher.publish_pin(draft)

        if published:
            history.mark_posted(tip, category["name"])
            excluded_ids.add(tip["id"])
            source = "AI-generated" if generated_by_ai else "static"
            print(
                f"Saved {source} content {tip['id']} to tip history."
            )
        else:
            print("Dry run / no confirmed publish: tip was NOT added to history.")

        processed += 1

    print(f"\nTip run complete. Processed {processed} Pin(s).")


if __name__ == "__main__":
    main()
