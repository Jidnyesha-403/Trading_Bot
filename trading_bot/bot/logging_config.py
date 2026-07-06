"""
Logging configuration.

Sets up a single logger that writes:
  - INFO and above to the console (so the user sees what's happening)
  - DEBUG and above to a rotating log file (so every request/response/error
    is captured for later review, without spamming the terminal)

Call setup_logger() once at application startup and get_logger(__name__)
everywhere else.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from bot.config import Config

_CONFIGURED = False


def setup_logger():
    """Idempotently configure the root 'trading_bot' logger."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    os.makedirs(Config.LOG_DIR, exist_ok=True)
    log_path = os.path.join(Config.LOG_DIR, Config.LOG_FILE)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler: keeps logs bounded (5 files x 2MB) instead of
    # growing forever, while still capturing full request/response detail.
    file_handler = RotatingFileHandler(
        log_path, maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _CONFIGURED = True


def get_logger(name):
    """Return a child logger under the 'trading_bot' namespace."""
    setup_logger()
    return logging.getLogger(f"trading_bot.{name}")
