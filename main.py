from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv(override=True)

from config import CONFIG
from core.logger import get_logger
from managers import backtest_manager, paper_manager, live_manager

logger = get_logger()

def main():
    mode = CONFIG.get("mode", "BACKTEST").upper()
    print(f"[STATUS] Starting Optimus in {mode} mode...")
    if mode == "BACKTEST":
        backtest_manager.run(CONFIG)
    elif mode == "PAPER":
        paper_manager.run(CONFIG)
    elif mode == "LIVE":
        live_manager.run(CONFIG)
    else:
        raise SystemExit(f"Unknown OPTIMUS_MODE={mode}")

if __name__ == "__main__":
    main()
