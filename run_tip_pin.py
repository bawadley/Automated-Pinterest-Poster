import argparse
import random

from ai_content_generator import AIContentGenerator
from config import load_config
from pinterest_browser import PinterestBrowserPublisher
from tip_builder import build_tip_draft, load_tip_config
from tip_history import TipHistory


CONTENT_TYPES = ["tip", "quote", "question", "quiz"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create and publish non-affiliate Pinterest content Pins."
    )
    parser.add_argument(
        "--category",
        action="append",
        dest="categories",
        help=(
            "Category filter. Repeat to allow multiple categories. "
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
            "Default content type when --pin-type is not supplied: "
            "'tip', 'quote', 'question', 'quiz', or 'all'."
        ),
    )
    parser.add_argument(
        "--count",
        "--pins",
        dest="count",
        type=int,
        default=1,
        help="Number of non-affiliate Pins to create in this run.",
    )
    parser.add_argument(
        "--pin-type",
        action="append",
        choices=["tip", "quote", "question", "quiz", "random"],
        dest="pin_types",
        help=(
            "Choose the type for one Pin slot. Repeat once per Pin. "
            "Example: --pin-type quiz --pin-type question --pin-type random"
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
        help="List available non-affiliate categories and exit.",
    )
    return parser.parse_args()


def _category_type(category):
    return category.get("content_type", "tip")


def _matches_base(category, filters, vertical):
    if vertical and category.get("vertical") != vertical:
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


def _resolve_requested_types(args):
    if args.count < 1:
        raise RuntimeError("--count / --pins must be at least 1.")

    if args.pin_types:
        if len(args.pin_types) != args.count:
            raise RuntimeError(
                "When using --pin-type, provide exactly one --pin-type "
                f"for each requested Pin. Requested {args.count} Pin(s) "
                f"but received {len(args.pin_types)} type selection(s)."
            )
        return list(args.pin_types)

    if args.content_type == "all":
        return ["random"] * args.count

    return [args.content_type] * args.count


def _choose_category(
    base_categories,
    requested_type,
    used_category_names,
    excluded_ids,
    static_only=False,
):
    if requested_type == "random":
        available_types = []
        for content_type in CONTENT_TYPES:
            candidates = [
                category
                for category in base_categories
                if _category_type(category) == content_type
            ]
            if static_only:
                candidates = [
                    category
                    for category in candidates
                    if _pick_fresh_tip(category, excluded_ids) is not None
                ]
            if candidates:
                available_types.append(content_type)

        if not available_types:
            return None, None

        requested_type = random.choice(available_types)

    candidates = [
        category
        for category in base_categories
        if _category_type(category) == requested_type
    ]

    if static_only:
        candidates = [
            category
            for category in candidates
            if _pick_fresh_tip(category, excluded_ids) is not None
        ]

    if not candidates:
        return None, requested_type

    unused = [
        category
        for category in candidates
        if category.get("name") not in used_category_names
    ]
    pool = unused if unused else candidates

    return random.choice(pool), requested_type


def main():
    # Some eBay titles contain Unicode characters outside Windows cp1252.
    # Preserve readable output without letting terminal encoding abort a run.
    import sys
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    args = parse_args()
    app_cfg = load_config()
    tip_cfg = load_tip_config()

    if args.list_categories:
        print("\nAvailable non-affiliate categories:\n")
        for category in tip_cfg.get("tip_categories", []):
            content_type = _category_type(category)
            print(
                f"- {category['name']} "
                f"[{category.get('vertical', '')} | {content_type}]"
            )
        return

    requested_types = _resolve_requested_types(args)

    base_categories = [
        category
        for category in tip_cfg.get("tip_categories", [])
        if _matches_base(
            category,
            args.categories,
            args.vertical,
        )
    ]

    if not base_categories:
        raise RuntimeError("No non-affiliate categories matched your filters.")

    settings = tip_cfg.get("tip_settings", {})
    history = TipHistory(
        settings.get("history_db_path", "data/tip_history.db")
    )
    cooldown_days = int(settings.get("cooldown_days", 365))
    excluded_ids = history.recent_tip_ids(cooldown_days)
    output_dir = settings.get("output_dir", "output/tip_images")

    print("\n=== Pinterest Non-Affiliate Content Automation ===")
    print(f"Requested Pins: {args.count}")
    print("Pin plan: " + ", ".join(requested_types))
    if args.categories:
        print("Allowed categories: " + ", ".join(args.categories))
    if args.vertical:
        print(f"Vertical: {args.vertical}")
    print(
        f"Tip history: {history.posted_count()} saved | "
        f"{len(excluded_ids)} excluded for {cooldown_days} days"
    )
    print(
        f"Content repeat cooldown: {cooldown_days} days "
        "(older ideas may be reused after this window)"
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

    publisher = PinterestBrowserPublisher(app_cfg["pinterest"])
    processed = 0
    used_category_names = set()
    session_previous_items = history.recent_posted_items(
        cooldown_days=cooldown_days,
        limit=100,
    )

    for index, requested_type in enumerate(requested_types, start=1):
        category, resolved_type = _choose_category(
            base_categories,
            requested_type,
            used_category_names,
            excluded_ids,
            static_only=not ai_enabled,
        )

        if category is None:
            print(
                f"\nNo eligible {resolved_type or requested_type} category "
                f"was available for Pin {index}."
            )
            continue

        used_category_names.add(category["name"])

        print(
            f"\n=== Content Pin {index}/{len(requested_types)}: "
            f"{category['name']} ==="
        )
        if requested_type == "random":
            print(f"Random type selected: {resolved_type}")
        print(f"Content type: {resolved_type}")

        tip = None
        generated_by_ai = False

        if ai_enabled:
            try:
                print(f"Generating fresh AI {resolved_type}...")
                tip = ai_generator.generate(
                    category,
                    previous_items=session_previous_items,
                )
                generated_by_ai = True
                print("AI content generated and passed duplicate checks.")
            except Exception as exc:
                print(f"WARNING: AI generation failed: {exc}")
                print(
                    "Falling back to the prewritten content library "
                    "for this Pin."
                )

        if tip is None:
            tip = _pick_fresh_tip(category, excluded_ids)

        if not tip:
            print(
                f"No unused static content remains in category: "
                f"{category['name']}"
            )
            continue

        print(f"Tip ID: {tip['id']}")
        print(f"Title: {tip['title']}")

        if resolved_type == "quote":
            print(f"Quote: {tip['quote']}")
        elif resolved_type == "question":
            print(f"Prompt: {tip['prompt']}")
        elif resolved_type == "quiz":
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

        # Prevent duplicates inside the same batch even during dry runs.
        excluded_ids.add(tip["id"])
        session_previous_items.insert(
            0,
            {
                "tip_id": tip["id"],
                "category": category["name"],
                "title": tip["title"],
                "content": tip,
                "last_posted": "current-session",
            },
        )

        if published:
            history.mark_posted(tip, category["name"])
            source = "AI-generated" if generated_by_ai else "static"
            print(
                f"Saved {source} content {tip['id']} to tip history."
            )
        else:
            print(
                "Dry run / no confirmed publish: content was NOT added "
                "to persistent history."
            )

        processed += 1

    print(f"\nContent run complete. Processed {processed} Pin(s).")


if __name__ == "__main__":
    main()
