"""
Binance Futures Testnet (USDT-M) API client.

This is the only module that knows how to talk HTTP to Binance. Everything
above this layer (orders.py, cli.py) works with plain Python dicts and
never touches signing, headers, or URLs directly. That separation is what
lets us swap transport (requests -> httpx, or REST -> python-binance)
without touching business logic.
"""

import hashlib
import hmac
import time
from urllib.parse import urlencode

import requests

from bot.config import Config
from bot.logging_config import get_logger

logger = get_logger("client")


class BinanceAPIError(Exception):
    """Raised when Binance returns a non-2xx response with an error body."""

    def __init__(self, status_code, code, message):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code} (HTTP {status_code}): {message}")


class BinanceNetworkError(Exception):
    """Raised for connection/timeout problems reaching Binance at all."""


class FuturesTestnetClient:
    """Thin wrapper around the Binance Futures Testnet REST API."""

    def __init__(self, api_key=None, api_secret=None, base_url=None):
        self.api_key = api_key or Config.API_KEY
        self.api_secret = api_secret or Config.API_SECRET
        self.base_url = base_url or Config.BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    # ------------------------------------------------------------------ #
    # Low-level request plumbing
    # ------------------------------------------------------------------ #
    def _get_server_time(self) -> int:
        """Fetch Binance server time to avoid local clock skew issues."""
        response = self.session.get(f"{self.base_url}/fapi/v1/time", timeout=Config.REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
        return int(payload["serverTime"])

    def _sign(self, params: dict) -> dict:
        """Attach timestamp, recvWindow, and an HMAC-SHA256 signature."""
        params = dict(params)
        params["timestamp"] = self._get_server_time()
        params["recvWindow"] = Config.RECV_WINDOW
        query_string = urlencode(params, doseq=True)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(self, method: str, path: str, params: dict = None, signed: bool = False):
        params = params or {}
        url = f"{self.base_url}{path}"

        if signed:
            params = self._sign(params)

        logger.debug("REQUEST %s %s params=%s", method, url, _redact(params))

        try:
            response = self.session.request(
                method, url, params=params, timeout=Config.REQUEST_TIMEOUT
            )
        except requests.exceptions.RequestException as exc:
            logger.error("NETWORK ERROR calling %s %s: %s", method, url, exc)
            raise BinanceNetworkError(str(exc)) from exc

        logger.debug("RESPONSE %s %s status=%s body=%s", method, url, response.status_code, response.text)

        if not response.ok:
            try:
                body = response.json()
                code = body.get("code")
                message = body.get("msg", response.text)
            except ValueError:
                code, message = None, response.text
            logger.error(
                "API ERROR %s %s -> HTTP %s code=%s msg=%s",
                method, url, response.status_code, code, message,
            )
            raise BinanceAPIError(response.status_code, code, message)

        return response.json()

    # ------------------------------------------------------------------ #
    # Public endpoints
    # ------------------------------------------------------------------ #
    def ping(self):
        """Basic connectivity check (unsigned)."""
        return self._request("GET", "/fapi/v1/ping")

    def get_exchange_info(self):
        """Symbol metadata (filters, precision) - unsigned."""
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def get_symbol_filters(self, symbol: str) -> dict:
        """Return the LOT_SIZE / PRICE_FILTER dict for one symbol, or {}."""
        info = self.get_exchange_info()
        for s in info.get("symbols", []):
            if s.get("symbol") == symbol:
                return {f["filterType"]: f for f in s.get("filters", [])}
        return {}

    # ------------------------------------------------------------------ #
    # Signed (account/trading) endpoints
    # ------------------------------------------------------------------ #
    def place_order(self, **params) -> dict:
        """
        Place a new order. Accepts any valid Binance Futures order params,
        e.g. symbol, side, type, quantity, price, timeInForce, stopPrice.
        """
        clean_params = {k: v for k, v in params.items() if v is not None}
        return self._request("POST", "/fapi/v1/order", clean_params, signed=True)

    def get_order(self, symbol: str, order_id: int) -> dict:
        """Query a single order's current status."""
        return self._request(
            "GET", "/fapi/v1/order", {"symbol": symbol, "orderId": order_id}, signed=True
        )

    def get_account_balance(self):
        """Account balance snapshot - useful for sanity checks / debugging."""
        return self._request("GET", "/fapi/v2/balance", signed=True)


def _redact(params: dict) -> dict:
    """Never write API secrets/signatures in full to logs."""
    redacted = dict(params)
    if "signature" in redacted:
        redacted["signature"] = redacted["signature"][:6] + "...redacted"
    return redacted
