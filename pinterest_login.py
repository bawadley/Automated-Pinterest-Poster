from config import load_config
from pinterest_browser import PinterestBrowserPublisher


if __name__ == "__main__":
    cfg = load_config()["pinterest"]
    PinterestBrowserPublisher(cfg).login_once()
