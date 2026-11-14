import base64
import time
import requests


OAUTH_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
DEFAULT_SCOPE = "https://api.ebay.com/oauth/api_scope"


class EbayTokenManager:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self._access_token = None
        self._expires_at = 0.0

    def _basic_auth(self):
        raw = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        return base64.b64encode(raw).decode("ascii")

    def get_user_access_token(self, force_refresh: bool = False) -> str:
        if (
            not force_refresh
            and self._access_token
            and time.time() < self._expires_at - 300
        ):
            return self._access_token

        response = requests.post(
            OAUTH_TOKEN_URL,
            headers={
                "Authorization": f"Basic {self._basic_auth()}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "scope": DEFAULT_SCOPE,
            },
            timeout=30,
        )

        if not response.ok:
            raise RuntimeError(
                "Could not refresh eBay OAuth token. "
                f"HTTP {response.status_code}: {response.text}"
            )

        data = response.json()
        self._access_token = data["access_token"]
        self._expires_at = time.time() + int(data.get("expires_in", 7200))
        return self._access_token
