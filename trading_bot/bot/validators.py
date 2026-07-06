"""
Input validation.

Keeping validation separate from both the CLI parser and the order logic
means the same rules can be reused (e.g. by a future web UI) and unit
tested in isolation.
"""

import re

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP", "STOP_MARKET"}
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")


class ValidationError(ValueError):
    """Raised when user-supplied CLI input fails validation."""


def validate_symbol(symbol: str) -> str:
    symbol = (symbol or "").strip().upper()
    if not SYMBOL_PATTERN.match(symbol):
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Expected something like 'BTCUSDT' "
            "(uppercase letters/digits, 5-20 chars)."
        )
    return symbol


def validate_side(side: str) -> str:
    side = (side or "").strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"Invalid side '{side}'. Must be one of {sorted(VALID_SIDES)}.")
    return side


def validate_order_type(order_type: str) -> str:
    order_type = (order_type or "").strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of {sorted(VALID_ORDER_TYPES)}."
        )
    return order_type


def validate_quantity(quantity) -> float:
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity must be a number, got '{quantity}'.")
    if qty <= 0:
        raise ValidationError(f"Quantity must be positive, got {qty}.")
    return qty


def validate_price(price, order_type: str):
    """Price is required for LIMIT and STOP orders, optional for others."""
    if order_type in ("LIMIT", "STOP"):
        if price is None:
            raise ValidationError(f"Price is required for {order_type} orders.")
        try:
            price_val = float(price)
        except (TypeError, ValueError):
            raise ValidationError(f"Price must be a number, got '{price}'.")
        if price_val <= 0:
            raise ValidationError(f"Price must be positive, got {price_val}.")
        return price_val

    if price is not None:
        # Provided but not required (e.g. MARKET) - ignore rather than fail.
        return None
    return None


def validate_stop_price(stop_price, order_type: str):
    """Stop price is required for STOP and STOP_MARKET orders."""
    if order_type in ("STOP", "STOP_MARKET"):
        if stop_price is None:
            raise ValidationError(f"--stop-price is required for {order_type} orders.")
        try:
            sp = float(stop_price)
        except (TypeError, ValueError):
            raise ValidationError(f"Stop price must be a number, got '{stop_price}'.")
        if sp <= 0:
            raise ValidationError(f"Stop price must be positive, got {sp}.")
        return sp
    return None


def validate_order_input(symbol, side, order_type, quantity, price=None, stop_price=None):
    """Run all validators and return a clean, normalized dict of order args."""
    clean_symbol = validate_symbol(symbol)
    clean_side = validate_side(side)
    clean_type = validate_order_type(order_type)
    clean_qty = validate_quantity(quantity)
    clean_price = validate_price(price, clean_type)
    clean_stop_price = validate_stop_price(stop_price, clean_type)

    return {
        "symbol": clean_symbol,
        "side": clean_side,
        "order_type": clean_type,
        "quantity": clean_qty,
        "price": clean_price,
        "stop_price": clean_stop_price,
    }
