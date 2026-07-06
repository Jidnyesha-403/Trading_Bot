"""
Order placement logic.

This module sits between the CLI and the raw API client: it takes already
validated input, builds the correct Binance order payload for each order
type, logs the request/response, and returns a clean result object the
CLI can print. No argparse or print() calls belong in here - that keeps
this layer reusable (e.g. from a script, a test, or a future web API).
"""

from dataclasses import dataclass, field
from typing import Optional

from bot.client import BinanceAPIError, BinanceNetworkError, FuturesTestnetClient
from bot.logging_config import get_logger

logger = get_logger("orders")


@dataclass
class OrderResult:
    success: bool
    request: dict
    response: Optional[dict] = None
    error: Optional[str] = None

    def summary_lines(self):
        """Human-readable lines for CLI output."""
        lines = ["--- Order Request ---"]
        for k, v in self.request.items():
            if v is not None:
                lines.append(f"  {k}: {v}")

        if self.success:
            lines.append("--- Order Response ---")
            r = self.response or {}
            lines.append(f"  orderId     : {r.get('orderId')}")
            lines.append(f"  status      : {r.get('status')}")
            lines.append(f"  executedQty : {r.get('executedQty')}")
            avg_price = r.get("avgPrice")
            if avg_price is not None:
                lines.append(f"  avgPrice    : {avg_price}")
            lines.append("RESULT: SUCCESS - order placed on Binance Futures Testnet.")
        else:
            lines.append(f"RESULT: FAILURE - {self.error}")

        return lines


class OrderService:
    """Builds Binance order payloads and places them via the API client."""

    def __init__(self, client: FuturesTestnetClient = None):
        self.client = client or FuturesTestnetClient()

    def _build_payload(self, symbol, side, order_type, quantity, price, stop_price):
        payload = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            payload["price"] = price
            # GTC (Good-Til-Cancelled) is the standard default time-in-force
            # for limit orders that aren't meant to expire immediately.
            payload["timeInForce"] = "GTC"
        elif order_type == "STOP":
            payload["price"] = price
            payload["stopPrice"] = stop_price
            payload["timeInForce"] = "GTC"
        elif order_type == "STOP_MARKET":
            payload["stopPrice"] = stop_price
        # MARKET needs nothing extra.

        return payload

    def place_order(self, symbol, side, order_type, quantity, price=None, stop_price=None) -> OrderResult:
        """
        Place an order on Binance Futures Testnet.

        Expects already-validated arguments (see bot.validators). Any API
        or network failure is caught here and returned as a failed
        OrderResult rather than raised, so the CLI layer never has to
        know about Binance-specific exception types.
        """
        payload = self._build_payload(symbol, side, order_type, quantity, price, stop_price)

        logger.info("Placing order: %s", payload)

        try:
            response = self.client.place_order(**payload)
            logger.info(
                "Order placed successfully: orderId=%s status=%s",
                response.get("orderId"), response.get("status"),
            )
            return OrderResult(success=True, request=payload, response=response)

        except BinanceAPIError as exc:
            logger.error("Order rejected by Binance: %s", exc)
            return OrderResult(success=False, request=payload, error=str(exc))

        except BinanceNetworkError as exc:
            logger.error("Network failure while placing order: %s", exc)
            return OrderResult(
                success=False, request=payload,
                error=f"Network error reaching Binance Futures Testnet: {exc}",
            )

        except Exception as exc:  # noqa: BLE001 - last-resort safety net
            logger.exception("Unexpected error while placing order")
            return OrderResult(success=False, request=payload, error=f"Unexpected error: {exc}")
