from dataclasses import dataclass, asdict, field


@dataclass
class EbayProduct:
    search_category: str
    item_id: str
    legacy_item_id: str
    title: str
    price: float
    currency: str
    quantity_sold: int
    seller_username: str
    seller_feedback_percent: float
    image_url: str
    item_url: str
    affiliate_url: str
    ebay_category_id: str
    condition: str

    def to_dict(self):
        return asdict(self)


@dataclass
class PinDraft:
    title: str
    description: str
    affiliate_url: str
    image_path: str
    board_name: str
    topics: list[str] = field(default_factory=list)
