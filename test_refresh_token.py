from config import load_config, require_ebay_config
from token_manager import EbayTokenManager


def main():
    cfg = load_config()
    require_ebay_config(cfg)
    env = cfg["env"]

    manager = EbayTokenManager(
        env["client_id"],
        env["client_secret"],
        env["refresh_token"],
    )

    token = manager.get_user_access_token(force_refresh=True)
    print("SUCCESS: eBay refresh token worked.")
    print(f"New access token received ({len(token)} characters).")
    print("The token itself is intentionally not printed.")


if __name__ == "__main__":
    main()
