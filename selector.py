from collections import defaultdict

from scoring import score_product


def rank_products(products, weights=None):
    ranked = []

    for product in products:
        score = score_product(product, weights=weights)

        if score["blocked"]:
            continue

        ranked.append({
            "product": product,
            "score": score,
        })

    ranked.sort(
        key=lambda row: (
            row["score"]["total"],
            row["product"].quantity_sold,
            row["product"].price,
        ),
        reverse=True,
    )

    return ranked


def select_diverse_products(products, count=5, weights=None):
    """
    Selects one top product per search category first.
    If more slots remain, fills them with the next-best overall products.

    This keeps the daily batch diverse while still rewarding the strongest
    listings overall.
    """
    count = max(int(count), 1)
    ranked = rank_products(products, weights=weights)

    by_category = defaultdict(list)
    for row in ranked:
        by_category[row["product"].search_category].append(row)

    selected = []
    selected_ids = set()

    # Pass 1: take the best product from each category.
    category_best = []
    for category, rows in by_category.items():
        if rows:
            category_best.append(rows[0])

    # Sort the category winners by score so the strongest categories still lead.
    category_best.sort(
        key=lambda row: (
            row["score"]["total"],
            row["product"].quantity_sold,
            row["product"].price,
        ),
        reverse=True,
    )

    for row in category_best:
        if len(selected) >= count:
            break

        product_id = row["product"].item_id or row["product"].legacy_item_id
        if product_id in selected_ids:
            continue

        selected.append(row)
        selected_ids.add(product_id)

    # Pass 2: fill any remaining slots with the next-best overall products.
    if len(selected) < count:
        for row in ranked:
            if len(selected) >= count:
                break

            product_id = row["product"].item_id or row["product"].legacy_item_id
            if product_id in selected_ids:
                continue

            selected.append(row)
            selected_ids.add(product_id)

    return selected


def select_top_products(products, count=5, weights=None):
    """
    Backward-compatible wrapper.
    Existing code can keep calling select_top_products().
    """
    return select_diverse_products(
        products,
        count=count,
        weights=weights,
    )
