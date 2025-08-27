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
    start = end - timedelta(days=7)
    start_s, end_s = _date_str(start), _date_str(end)

    equity = float(os.getenv("OPTIMUS_START_EQUITY", config.get("account",{}).get("starting_equity", 10000.0)))

    feed = _pick_feed(config)
    option_symbol = feed.pick_option_instrument(config)
    perp_symbol = os.getenv("OPTIMUS_UNDERLYING", config.get("market",{}).get("perp_symbol","ETHUSD"))

    logger.info(f"Fetching option data for {option_symbol}...")
    opt_15m = feed.get_option_ohlcv(option_symbol, "15min", start_s, end_s)
    
    logger.info(f"Fetching perp data for {perp_symbol}...")
    perp_1h = feed.get_perp_ohlcv(perp_symbol, "1h", start_s, end_s)

    if opt_15m.empty:
        suggestion = (f"No option candles found. Suggestions:\n"
                     f"1. Check if option symbol/product_id '{option_symbol}' exists\n"
                     f"2. Try a different time range (current: {start_s} to {end_s})\n"
                     f"3. Enable OPTIMUS_AUTO_SELECT=1 for automatic option selection\n"
                     f"4. Set OPTIMUS_OPTION_PRODUCT_ID or OPTIMUS_OPTION_SYMBOL explicitly\n"
                     f"5. Check your internet connection and API endpoints")
        logger.error(f"No option candles for {option_symbol} in [{start_s} → {end_s}]")
        logger.info(suggestion)
        raise RuntimeError(f"No option candles for {option_symbol} in [{start_s} → {end_s}]. {suggestion}")

    if perp_1h.empty:
        logger.warning(f"No perpetual candles for {perp_symbol} - continuing with option data only")
    else:
        logger.info(f"Loaded {len(perp_1h)} perpetual candles and {len(opt_15m)} option candles")

    strategy = OptimusStrategy()
    risk = RiskManager(max_position_notional=equity*0.2, max_daily_loss=equity*0.05, allow_both_sides=False)

    trades = []
    for ts, row in opt_15m.iterrows():
        price = float(row["close"]) if "close" in row else 1.0
        signal = strategy.generate_signal(price=price, time=ts)
        if not signal: continue
        if not risk.can_trade(side=signal.side, price=price, time=ts): continue
        trade = strategy.execute_signal(signal, price=price, time=ts, mode="BACKTEST")
        if trade: trades.append(trade); log_trade(trade)

    logger.info(f"Backtest (feed) complete. Trades: {len(trades)} → logs/trades.csv")
