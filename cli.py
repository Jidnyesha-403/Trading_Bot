#!/usr/bin/env python3
"""Compatibility entry point for running the bot from the workspace root."""

import runpy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent / "trading_bot"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    runpy.run_path(str(PROJECT_ROOT / "cli.py"), run_name="__main__")
