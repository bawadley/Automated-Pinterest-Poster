from config import load_config
from models import PinDraft
from pinterest_browser import PinterestBrowserPublisher


if __name__ == "__main__":
    cfg = load_config()["pinterest"]

    draft = PinDraft(
        title="Honda CB750 Test Pin - Browser Automation",
        description=(
            "Test description for the combined eBay + Pinterest automation project."
        ),
        affiliate_url="https://www.ebay.com/",
        image_path="test_pin.jpg",
        board_name=cfg["board_name"],
    )

    PinterestBrowserPublisher(cfg).publish_pin(draft)
