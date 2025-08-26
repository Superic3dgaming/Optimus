from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from core.logger import get_logger, log_trade
from core.strategy import OptimusStrategy
from core.risk import RiskManager
from datafeeds.delta_datafeed import DeltaDataFeed

logger = get_logger()

def _date_str(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _pick_feed(config) -> DeltaDataFeed:
    base = os.getenv("OPTIMUS_API_BASE", "https://api.delta.exchange")
    autodiscover = not (os.getenv("OPTIMUS_DISABLE_DISCOVERY", "").strip().lower() in ("1","true","yes"))
    return DeltaDataFeed(base_url=base, autodiscover=autodiscover)

def run(config) -> None:
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=3)
    start_s, end_s = _date_str(start), _date_str(end)

    equity = float(os.getenv("OPTIMUS_START_EQUITY", config.get("account",{}).get("starting_equity", 10000.0)))

    feed = _pick_feed(config)
    option_symbol = feed.pick_option_instrument(config)
    perp_symbol = os.getenv("OPTIMUS_UNDERLYING", config.get("market",{}).get("perp_symbol","ETHUSD"))

    opt_15m = feed.get_option_ohlcv(option_symbol, "15min", start_s, end_s)

    strategy = OptimusStrategy()
    risk = RiskManager(max_position_notional=equity*0.2, max_daily_loss=equity*0.05, allow_both_sides=False)

    trades = []
    for ts, row in opt_15m.iterrows():
        price = float(row["close"]) if "close" in row else 1.0
        signal = strategy.generate_signal(price=price, time=ts)
        if not signal: continue
        if not risk.can_trade(side=signal.side, price=price, time=ts): continue
        trade = strategy.execute_signal(signal, price=price, time=ts, mode="PAPER")
        if trade: trades.append(trade); log_trade(trade)

    logger.info(f"Paper run complete. Trades: {len(trades)} → logs/trades.csv")
