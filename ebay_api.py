import base64
import re
import uuid
import requests
import xml.etree.ElementTree as ET

from models import EbayProduct
from token_manager import EbayTokenManager


BROWSE_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
OAUTH_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
TRADING_URL = "https://api.ebay.com/ws/api.dll"


class EbayAPI:
    def __init__(self, env: dict):
        self.client_id = env["client_id"]
        self.client_secret = env["client_secret"]
        self.campaign_id = env["epn_campaign_id"]
        self.marketplace_id = env["marketplace_id"]

        self.token_manager = EbayTokenManager(
            env["client_id"],
            env["client_secret"],
            env["refresh_token"],
        )
        self._application_token = None

    def get_application_token(self):
        if self._application_token:
            return self._application_token

        basic = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode("utf-8")
        ).decode("ascii")

        response = requests.post(
            OAUTH_TOKEN_URL,
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope",
            },
            timeout=30,
        )
        response.raise_for_status()
        self._application_token = response.json()["access_token"]
        return self._application_token

    @staticmethod
    def _legacy_id(rest_item_id: str) -> str:
        match = re.search(r"\|(\d{9,})\|", rest_item_id or "")
        if match:
            return match.group(1)
        return rest_item_id if (rest_item_id or "").isdigit() else ""

    @staticmethod
    def _prefer_large_ebay_image(url: str) -> str:
        """
        eBay Picture Services URLs often encode the served size in the final
        path component (for example s-l225, s-l500, s-l1600). Request the
        large variant when the image is hosted by eBay.
        """
        if not url:
            return ""

        if "ebayimg.com" not in url.lower():
            return url

        return re.sub(
            r"s-l\d+(?=\.(?:jpg|jpeg|png|webp)(?:\?|$))",
            "s-l1600",
            url,
            flags=re.IGNORECASE,
        )

    def _trading_get_item(self, legacy_item_id: str, token: str):
        body = f"""<?xml version="1.0" encoding="utf-8"?>
<GetItemRequest xmlns="urn:ebay:apis:eBLBaseComponents">
  <RequesterCredentials>
    <eBayAuthToken>{token}</eBayAuthToken>
  </RequesterCredentials>
  <ItemID>{legacy_item_id}</ItemID>
  <DetailLevel>ReturnAll</DetailLevel>
</GetItemRequest>"""
        return requests.post(
            TRADING_URL,
            headers={
                "X-EBAY-API-CALL-NAME": "GetItem",
                "X-EBAY-API-SITEID": "0",
                "X-EBAY-API-COMPATIBILITY-LEVEL": "1489",
                "Content-Type": "text/xml",
            },
            data=body.encode("utf-8"),
            timeout=30,
        )

    def get_listing_details(self, legacy_item_id: str) -> dict:
        if not legacy_item_id:
            return {"quantity_sold": 0, "image_url": ""}

        token = self.token_manager.get_user_access_token()
        response = self._trading_get_item(legacy_item_id, token)

        if response.status_code in (401, 403):
            token = self.token_manager.get_user_access_token(force_refresh=True)
            response = self._trading_get_item(legacy_item_id, token)

        response.raise_for_status()

        root = ET.fromstring(response.text)
        ns = {"e": "urn:ebay:apis:eBLBaseComponents"}
        ack = root.findtext("e:Ack", default="", namespaces=ns)

        if ack not in ("Success", "Warning"):
            message = root.findtext(
                ".//e:LongMessage",
                default="Unknown Trading API error",
                namespaces=ns,
            )
            if "token" in message.lower():
                token = self.token_manager.get_user_access_token(force_refresh=True)
                response = self._trading_get_item(legacy_item_id, token)
                response.raise_for_status()
                root = ET.fromstring(response.text)
                ack = root.findtext("e:Ack", default="", namespaces=ns)
                if ack not in ("Success", "Warning"):
                    message = root.findtext(
                        ".//e:LongMessage",
                        default="Unknown Trading API error",
                        namespaces=ns,
                    )
                    raise RuntimeError(message)
            else:
                raise RuntimeError(message)

        sold_text = root.findtext(
            ".//e:Item/e:SellingStatus/e:QuantitySold",
            default="0",
            namespaces=ns,
        )
        try:
            sold = int(sold_text)
        except Exception:
            sold = 0

        picture_urls = root.findall(
            ".//e:Item/e:PictureDetails/e:PictureURL",
            namespaces=ns,
        )
        listing_image = ""
        for picture in picture_urls:
            if picture.text and picture.text.strip():
                listing_image = self._prefer_large_ebay_image(
                    picture.text.strip()
                )
                break

        return {
            "quantity_sold": sold,
            "image_url": listing_image,
        }

    def get_quantity_sold(self, legacy_item_id: str) -> int:
        """Backward-compatible wrapper used by any older callers."""
        return self.get_listing_details(legacy_item_id)["quantity_sold"]

    def search(
        self,
        category_name: str,
        query: str,
        category_id: str = "",
        limit: int = 20,
        progress_callback=None,
        excluded_ids=None,
    ):
        app_token = self.get_application_token()
        custom_id = f"pinterest-{uuid.uuid4().hex[:12]}"
        excluded_ids = {str(value) for value in (excluded_ids or set()) if value}

        headers = {
            "Authorization": f"Bearer {app_token}",
            "X-EBAY-C-MARKETPLACE-ID": self.marketplace_id,
            "X-EBAY-C-ENDUSERCTX": (
                f"affiliateCampaignId={self.campaign_id},"
                f"affiliateReferenceId={custom_id}"
            ),
        }

        target_count = min(max(int(limit), 1), 200)
        scan_page_size = min(max(target_count, 50), 200)
        offset = 0
        fresh_items = []
        skipped_posted = 0

        # Scan eBay's Best Match results in pages. Already-posted item IDs are
        # skipped before the slower Trading API detail lookup, and pagination
        # continues until we have a full fresh candidate batch.
        while len(fresh_items) < target_count:
            params = {
                "q": query,
                "limit": scan_page_size,
                "offset": offset,
            }
            if category_id:
                params["category_ids"] = category_id

            response = requests.get(
                BROWSE_SEARCH_URL,
                headers=headers,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            items = data.get("itemSummaries", [])
            if not items:
                break

            for item in items:
                rest_id = item.get("itemId", "")
                legacy_id = self._legacy_id(rest_id)

                if rest_id in excluded_ids or legacy_id in excluded_ids:
                    skipped_posted += 1
                    continue

                fresh_items.append(item)
                if len(fresh_items) >= target_count:
                    break

            total_available = int(data.get("total", 0) or 0)
            offset += scan_page_size

            if offset >= total_available or len(items) < scan_page_size:
                break

        if skipped_posted:
            print(
                f"  Skipped {skipped_posted} previously posted "
                f"listing{'s' if skipped_posted != 1 else ''}."
            )

        total_items = len(fresh_items)

        if progress_callback:
            progress_callback(0, total_items, "Checking fresh listing details")

        products = []
        for index, item in enumerate(fresh_items, start=1):
            rest_id = item.get("itemId", "")
            legacy_id = self._legacy_id(rest_id)

            try:
                details = self.get_listing_details(legacy_id)
                sold = details["quantity_sold"]
                listing_image_url = details["image_url"]
            except Exception as exc:
                print(f"\n  WARNING: listing details unavailable for {legacy_id}: {exc}")
                sold = 0
                listing_image_url = ""

            price = item.get("price", {}) or {}
            seller = item.get("seller", {}) or {}
            search_image = item.get("image", {}) or {}
            cats = item.get("categories", []) or []

            image_url = (
                listing_image_url
                or self._prefer_large_ebay_image(search_image.get("imageUrl", ""))
            )

            products.append(EbayProduct(
                search_category=category_name,
                item_id=rest_id,
                legacy_item_id=legacy_id,
                title=item.get("title", ""),
                price=float(price.get("value", 0) or 0),
                currency=price.get("currency", ""),
                quantity_sold=sold,
                seller_username=seller.get("username", ""),
                seller_feedback_percent=float(
                    seller.get("feedbackPercentage", 0) or 0
                ),
                image_url=image_url,
                item_url=item.get("itemWebUrl", ""),
                affiliate_url=(
                    item.get("itemAffiliateWebUrl", "")
                    or item.get("itemWebUrl", "")
                ),
                ebay_category_id=(
                    str(cats[0].get("categoryId", "")) if cats else ""
                ),
                condition=item.get("condition", ""),
            ))

            if progress_callback:
                progress_callback(
                    index,
                    total_items,
                    f"Checked {index}/{total_items} fresh listings",
                )

        return products
