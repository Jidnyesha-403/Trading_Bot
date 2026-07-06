import unittest
from unittest import mock

from bot.client import FuturesTestnetClient


class ClientTimestampTests(unittest.TestCase):
    def test_sign_uses_server_time_when_available(self):
        client = FuturesTestnetClient(api_key="test-key", api_secret="test-secret")

        with mock.patch.object(client, "_get_server_time", return_value=1710000000000):
            params = client._sign({"symbol": "BTCUSDT"})

        self.assertEqual(params["timestamp"], 1710000000000)
        self.assertIn("signature", params)


if __name__ == "__main__":
    unittest.main()
