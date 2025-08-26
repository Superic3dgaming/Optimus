from __future__ import annotations
import os
from core.logger import get_logger
from core.strategy import OptimusStrategy
from core.risk import RiskManager
from datafeeds.delta_datafeed import DeltaDataFeed

logger = get_logger()

def _pick_feed(config) -> DeltaDataFeed:
    base = os.getenv("OPTIMUS_API_BASE", "https://api.delta.exchange")
    autodiscover = not (os.getenv("OPTIMUS_DISABLE_DISCOVERY", "").strip().lower() in ("1","true","yes"))
    return DeltaDataFeed(base_url=base, autodiscover=autodiscover)

def run(config) -> None:
    feed = _pick_feed(config)
    option_symbol = feed.pick_option_instrument(config)
    perp_symbol = os.getenv("OPTIMUS_UNDERLYING", config.get("market",{}).get("perp_symbol","ETHUSD"))
    logger.info(f"LIVE started with option={option_symbol} perp={perp_symbol} (broker integration placeholder)")
