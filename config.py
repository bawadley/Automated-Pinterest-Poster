from pathlib import Path
import os
import yaml
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent


def _as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def load_config():
    load_dotenv(BASE_DIR / ".env")

    with open(BASE_DIR / "config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    cfg["env"] = {
        "client_id": os.getenv("EBAY_CLIENT_ID", ""),
        "client_secret": os.getenv("EBAY_CLIENT_SECRET", ""),
        "refresh_token": os.getenv("EBAY_REFRESH_TOKEN", ""),
        "epn_campaign_id": os.getenv("EBAY_EPN_CAMPAIGN_ID", ""),
        "marketplace_id": os.getenv("EBAY_MARKETPLACE_ID", "EBAY_US"),
        "runame": os.getenv("EBAY_RUNAME", ""),
        "output_dir": os.getenv("OUTPUT_DIR", "output"),
    }

    cfg["pinterest"] = {
        "board_name": os.getenv(
            "PINTEREST_BOARD_NAME",
            "Vintage Honda Motorcycle Parts",
        ),
        "profile_dir": os.getenv("PINTEREST_PROFILE_DIR", "data/pinterest_profile"),
        "headless": _as_bool(os.getenv("PINTEREST_HEADLESS", "false")),
        "dry_run": _as_bool(os.getenv("PINTEREST_DRY_RUN", "true"), True),
        "timeout_ms": int(os.getenv("PINTEREST_TIMEOUT_MS", "30000")),
        "create_pin_url": os.getenv(
            "PINTEREST_CREATE_PIN_URL",
            "https://www.pinterest.com/pin-creation-tool/",
        ),
    }

    return cfg


def require_ebay_config(cfg):
    required = {
        "EBAY_CLIENT_ID": cfg["env"]["client_id"],
        "EBAY_CLIENT_SECRET": cfg["env"]["client_secret"],
        "EBAY_REFRESH_TOKEN": cfg["env"]["refresh_token"],
        "EBAY_EPN_CAMPAIGN_ID": cfg["env"]["epn_campaign_id"],
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            "Missing .env values: " + ", ".join(missing)
        )
