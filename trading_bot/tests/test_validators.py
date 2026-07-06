"""
Unit tests for bot.validators.

Run with:  python -m unittest discover -s tests
These don't touch the network at all - they only exercise pure input
validation logic, so they're safe to run anywhere, anytime.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.validators import ValidationError, validate_order_input


class TestValidators(unittest.TestCase):
    def test_valid_market_order(self):
        result = validate_order_input("btcusdt", "buy", "market", "0.01")
        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertEqual(result["side"], "BUY")
        self.assertEqual(result["order_type"], "MARKET")
        self.assertEqual(result["quantity"], 0.01)
        self.assertIsNone(result["price"])

    def test_valid_limit_order(self):
        result = validate_order_input("ETHUSDT", "SELL", "LIMIT", "1.5", price="3000")
        self.assertEqual(result["price"], 3000.0)

    def test_limit_requires_price(self):
        with self.assertRaises(ValidationError):
            validate_order_input("BTCUSDT", "BUY", "LIMIT", "0.01")

    def test_stop_market_requires_stop_price(self):
        with self.assertRaises(ValidationError):
            validate_order_input("BTCUSDT", "SELL", "STOP_MARKET", "0.01")

    def test_invalid_symbol(self):
        with self.assertRaises(ValidationError):
            validate_order_input("bt", "BUY", "MARKET", "0.01")

    def test_invalid_side(self):
        with self.assertRaises(ValidationError):
            validate_order_input("BTCUSDT", "HOLD", "MARKET", "0.01")

    def test_negative_quantity(self):
        with self.assertRaises(ValidationError):
            validate_order_input("BTCUSDT", "BUY", "MARKET", "-1")

    def test_non_numeric_quantity(self):
        with self.assertRaises(ValidationError):
            validate_order_input("BTCUSDT", "BUY", "MARKET", "abc")


if __name__ == "__main__":
    unittest.main()
