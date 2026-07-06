"""
Configuration module.

Loads Binance Futures Testnet credentials and settings from environment
variables (optionally via a local .env file). Keeping configuration in one
place makes it easy to swap between testnet and mainnet later, and avoids
hardcoding secrets anywhere in the codebase.
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_KEY_PATTERN = re.compile(r"^[A-Za-z0-9]{16,64}$")
API_SECRET_PATTERN = re.compile(r"^[A-Za-z0-9]{32,128}$")


def _load_environment() -> None:
    """Load .env from the project root first, then fall back to the current directory."""
    candidates = [PROJECT_ROOT / ".env", Path.cwd() / ".env"]
    for candidate in candidates:
        if candidate.exists():
            load_dotenv(candidate, override=False)
            return

    # Fall back to default discovery if an explicit file was not found.
    load_dotenv()


# Load variables from a .env file in the project root (or current working dir), if present.
_load_environment()


class Config:
    """Holds runtime configuration for the trading bot."""

    # Binance Futures Demo Trading (USDT-M) base URL. Binance retired the
    # old GitHub-login testnet.binancefuture.com in favor of "Demo Trading"
    # inside a regular Binance.com account, served from this domain. Do
    # not point this at mainnet (fapi.binance.com) without re-reviewing
    # the whole client for safety.
    BASE_URL = os.getenv("BINANCE_FUTURES_BASE_URL", "https://demo-fapi.binance.com")

    API_KEY = os.getenv("BINANCE_API_KEY", "")
    API_SECRET = os.getenv("BINANCE_API_SECRET", "")

    # Network timeout (seconds) for every outbound HTTP request.
    REQUEST_TIMEOUT = float(os.getenv("BINANCE_REQUEST_TIMEOUT", "10"))

    # Allowed clock skew (ms) Binance tolerates for signed requests.
    RECV_WINDOW = int(os.getenv("BINANCE_RECV_WINDOW", "5000"))

    LOG_DIR = os.getenv("BOT_LOG_DIR", "logs")
    LOG_FILE = os.getenv("BOT_LOG_FILE", "trading_bot.log")

    @classmethod
    def validate(cls):
        """Fail fast with a clear message if credentials are missing or clearly placeholder."""
        api_key = (cls.API_KEY or "").strip()
        api_secret = (cls.API_SECRET or "").strip()

        if not api_key or not api_secret:
            raise EnvironmentError(
                "Missing BINANCE_API_KEY / BINANCE_API_SECRET. "
                "Set them as environment variables or in a .env file "
                "(see .env.example)."
            )

        placeholder_values = {
            "your_api_key_here",
            "your_testnet_api_key_here",
            "your_api_secret_here",
            "your_testnet_api_secret_here",
            "demo_api_key_here",
            "demo_api_secret_here",
        }
        if api_key.lower() in placeholder_values or any(token in api_key.lower() for token in ("your_", "your-", "placeholder", "example", "demo_")):
            raise EnvironmentError(
                "BINANCE_API_KEY looks like a placeholder. Generate a real Binance Demo Trading API key "
                "and paste it into the .env file."
            )
        if api_secret.lower() in placeholder_values or any(token in api_secret.lower() for token in ("your_", "your-", "placeholder", "example", "demo_")):
            raise EnvironmentError(
                "BINANCE_API_SECRET looks like a placeholder. Generate a real Binance Demo Trading API key "
                "and paste it into the .env file."
            )

        if not API_KEY_PATTERN.fullmatch(api_key):
            raise EnvironmentError(
                "BINANCE_API_KEY should be a generated Binance API key containing only letters and numbers."
            )
        if not API_SECRET_PATTERN.fullmatch(api_secret):
            raise EnvironmentError(
                "BINANCE_API_SECRET should be a generated Binance API secret containing only letters and numbers."
            )
