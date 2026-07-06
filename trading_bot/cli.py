#!/usr/bin/env python3
"""
CLI entry point for the Simplified Trading Bot (Binance Futures Testnet).

Examples
--------
Market order:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

Limit order:
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000

Stop-market order (bonus order type):
    python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.01 --stop-price 58000
"""

import argparse
import sys

from bot.config import Config
from bot.logging_config import get_logger, setup_logger
from bot.orders import OrderService
from bot.validators import ValidationError, validate_order_input

logger = get_logger("cli")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Place MARKET / LIMIT / STOP orders on Binance Futures Testnet (USDT-M).",
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"], help="Order side")
    parser.add_argument(
        "--type", dest="order_type", required=True,
        choices=["MARKET", "LIMIT", "STOP", "STOP_MARKET", "market", "limit", "stop", "stop_market"],
        help="Order type",
    )
    parser.add_argument("--quantity", required=True, help="Order quantity, e.g. 0.01")
    parser.add_argument("--price", default=None, help="Limit price (required for LIMIT/STOP orders)")
    parser.add_argument(
        "--stop-price", dest="stop_price", default=None,
        help="Stop trigger price (required for STOP/STOP_MARKET orders)",
    )
    return parser


def main(argv=None) -> int:
    setup_logger()
    parser = build_parser()
    args = parser.parse_args(argv)

    # 1. Validate input up front - fail fast with a friendly message
    try:
        clean = validate_order_input(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValidationError as exc:
        logger.error("Input validation failed: %s", exc)
        print(f"Invalid input: {exc}")
        return 1

    # 2. Confirm credentials are present before attempting any API call
    try:
        Config.validate()
    except EnvironmentError as exc:
        logger.error("Configuration error: %s", exc)
        print(f"Configuration error: {exc}")
        return 1

    # 3. Place the order
    service = OrderService()
    result = service.place_order(
        symbol=clean["symbol"],
        side=clean["side"],
        order_type=clean["order_type"],
        quantity=clean["quantity"],
        price=clean["price"],
        stop_price=clean["stop_price"],
    )

    for line in result.summary_lines():
        print(line)

    return 0 if result.success else 2


if __name__ == "__main__":
    sys.exit(main())
