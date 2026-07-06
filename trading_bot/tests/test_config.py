import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class ConfigDotenvTests(unittest.TestCase):
    def test_loads_env_from_project_root_when_cwd_is_elsewhere(self):
        values = dotenv_values(PROJECT_ROOT / ".env")

        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.dict(os.environ, {}, clear=True):
                old_cwd = os.getcwd()
                try:
                    os.chdir(temp_dir)
                    sys.modules.pop("bot.config", None)
                    import bot.config as config
                    importlib.reload(config)
                finally:
                    os.chdir(old_cwd)
                    sys.modules.pop("bot.config", None)

            self.assertEqual(config.Config.API_KEY, values.get("BINANCE_API_KEY", ""))
            self.assertEqual(config.Config.API_SECRET, values.get("BINANCE_API_SECRET", ""))

    def test_accepts_valid_binance_style_credentials(self):
        import bot.config as config

        with mock.patch.object(config.Config, "API_KEY", "AbCd1234EfGh5678IjKl9012MnOp3456"):
            with mock.patch.object(config.Config, "API_SECRET", "QwErTyUiOpAsDfGhJkLzXcVbNm1234567890QwErTyUiOpAsDfGhJkLzXcVb"):
                config.Config.validate()

    def test_rejects_placeholder_binance_credentials(self):
        import bot.config as config

        with mock.patch.object(config.Config, "API_KEY", "trading-bot"):
            with mock.patch.object(config.Config, "API_SECRET", "your_api_secret_here"):
                with self.assertRaises(EnvironmentError):
                    config.Config.validate()


if __name__ == "__main__":
    unittest.main()
