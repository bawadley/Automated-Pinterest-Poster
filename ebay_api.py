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

    def get_quantity_sold(self, legacy_item_id: str) -> int:
        if not legacy_item_id:
            return 0

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

        sold = root.findtext(
            ".//e:Item/e:SellingStatus/e:QuantitySold",
            default="0",
            namespaces=ns,
        )
        try:
            return int(sold)
        except Exception:
            return 0

    def search(self, category_name: str, query: str, category_id: str = "", limit: int = 20):
        app_token = self.get_application_token()
        custom_id = f"pinterest-{uuid.uuid4().hex[:12]}"

        headers = {
            "Authorization": f"Bearer {app_token}",
            "X-EBAY-C-MARKETPLACE-ID": self.marketplace_id,
            "X-EBAY-C-ENDUSERCTX": (
                f"affiliateCampaignId={self.campaign_id},"
                f"affiliateReferenceId={custom_id}"
            ),
        }

        params = {"q": query, "limit": min(max(int(limit), 1), 200)}
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

        products = []
        for item in data.get("itemSummaries", []):
            rest_id = item.get("itemId", "")
            legacy_id = self._legacy_id(rest_id)

            try:
                sold = self.get_quantity_sold(legacy_id)
            except Exception as exc:
                print(f"  WARNING: sold count unavailable for {legacy_id}: {exc}")
                sold = 0

            price = item.get("price", {}) or {}
            seller = item.get("seller", {}) or {}
            image = item.get("image", {}) or {}
            cats = item.get("categories", []) or []

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
                image_url=image.get("imageUrl", ""),
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

        return products
