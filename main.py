from __future__ import annotations
import os
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

from config import CONFIG
from core.logger import get_logger
from core.config_validation import validate_startup
from managers import backtest_manager, paper_manager, live_manager

logger = get_logger()

def main():
    # Perform startup validation
    if not validate_startup():
        logger.error("Startup validation failed. Please fix the issues above and try again.")
        sys.exit(1)
    
    mode = CONFIG.get("mode", "BACKTEST").upper()
    logger.info(f"Starting Optimus in {mode} mode...")
    
    try:
        if mode == "BACKTEST":
            backtest_manager.run(CONFIG)
        elif mode == "PAPER":
            paper_manager.run(CONFIG)
        elif mode == "LIVE":
            live_manager.run(CONFIG)
        else:
            raise SystemExit(f"Unknown OPTIMUS_MODE={mode}")
    except Exception as e:
        logger.error(f"Error running Optimus in {mode} mode: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
