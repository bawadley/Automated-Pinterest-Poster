import math


BLOCKED_KEYWORDS = [
    "service",
    "rebuild service",
    "clean & rebuild",
    "repair service",
    "manual",
    "brochure",
    "poster",
    "sticker",
]


HIGH_VALUE_KEYWORDS = [
    "carburetor",
    "carburetors",
    "carb",
    "gas tank",
    "fuel tank",
    "tank",
    "gauge",
    "gauges",
    "speedometer",
    "tachometer",
    "engine",
    "cylinder head",
    "exhaust",
    "seat",
    "oem",
]


def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def _contains_any(text: str, words):
    text = (text or "").lower()
    return any(word in text for word in words)


def blocked_listing(product) -> bool:
    title = (product.title or "").lower()
    return _contains_any(title, BLOCKED_KEYWORDS)


def demand_score(product, sold_cap=250):
    sold = max(int(product.quantity_sold or 0), 0)

    # Log scale so 200 sold is better than 20 sold,
    # but not 10x more important.
    if sold <= 0:
        return 0.0

    return _clamp(
        math.log1p(sold) / math.log1p(max(sold_cap, 1))
    )


def value_score(product, price_cap=500.0):
    price = max(float(product.price or 0), 0.0)
    return _clamp(price / max(float(price_cap), 1.0))


def seller_score(product):
    feedback = float(product.seller_feedback_percent or 0)

    # 97% => 0
    # 100% => 1
    return _clamp((feedback - 97.0) / 3.0)


def listing_quality_score(product):
    score = 0.0

    if product.image_url:
        score += 0.45

    if product.affiliate_url:
        score += 0.25

    if product.title and len(product.title.strip()) >= 20:
        score += 0.20

    if product.condition:
        score += 0.10

    return _clamp(score)


def category_value_score(product):
    title = (product.title or "").lower()
    category = (product.search_category or "").lower()

    combined = f"{title} {category}"

    if _contains_any(combined, HIGH_VALUE_KEYWORDS):
        return 1.0

    return 0.4


def score_product(product, weights=None):
    if blocked_listing(product):
        return {
            "total": -1.0,
            "blocked": True,
            "demand": 0.0,
            "value": 0.0,
            "category_value": 0.0,
            "seller": 0.0,
            "listing_quality": 0.0,
        }

    weights = weights or {
        "demand": 0.35,
        "value": 0.30,
        "category_value": 0.15,
        "seller": 0.10,
        "listing_quality": 0.10,
    }

    demand = demand_score(product)
    value = value_score(product)
    category_value = category_value_score(product)
    seller = seller_score(product)
    listing_quality = listing_quality_score(product)

    total = (
        demand * weights["demand"]
        + value * weights["value"]
        + category_value * weights["category_value"]
        + seller * weights["seller"]
        + listing_quality * weights["listing_quality"]
    )

    return {
        "total": total,
        "blocked": False,
        "demand": demand,
        "value": value,
        "category_value": category_value,
        "seller": seller,
        "listing_quality": listing_quality,
    }
