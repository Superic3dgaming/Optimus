from __future__ import annotations
import os, csv, logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

LOGS_DIR = "logs"
MAIN_LOG_FILE = os.path.join(LOGS_DIR, "optimus.log")
TRADES_CSV = os.path.join(LOGS_DIR, "trades.csv")
METRICS_CSV = os.path.join(LOGS_DIR, "metrics.csv")
EQUITY_CSV = os.path.join(LOGS_DIR, "equity.csv")

os.makedirs(LOGS_DIR, exist_ok=True)

_LOGGER: Optional[logging.Logger] = None

def _build_logger() -> logging.Logger:
    logger = logging.getLogger("optimus")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if logger.handlers:
        return logger
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(ch)
    fh = logging.FileHandler(MAIN_LOG_FILE)
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(fh)
    return logger

def get_logger() -> logging.Logger:
    global _LOGGER
    if _LOGGER is None:
        _LOGGER = _build_logger()
    return _LOGGER

def setup_logger() -> logging.Logger:  # compat
    return get_logger()

def _write_csv_row(path: str, header: list[str], row: Dict[str, Any]) -> None:
    new_file = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        if new_file:
            w.writeheader()
        safe_row = {k: row.get(k, "") for k in header}
        w.writerow(safe_row)

def log_trade(trade: Dict[str, Any]) -> None:
    header = ["time", "side", "signal", "qty", "entry_price", "sl_price", "tp_price", "exit_time", "exit_price", "pnl", "outcome", "status", "mode"]
    _write_csv_row(TRADES_CSV, header, trade)

def log_metric(metric: Dict[str, Any]) -> None:
    header = ["time", "name", "value", "context"]
    if "time" not in metric or not metric["time"]:
        metric = dict(metric)
        metric["time"] = datetime.now(timezone.utc).isoformat()
    _write_csv_row(METRICS_CSV, header, metric)

def log_equity(ts, equity_value: float, context: str = "") -> None:
    header = ["time", "equity", "context"]
    from datetime import datetime, timezone
    if ts is None:
        ts = datetime.now(timezone.utc)
    row = {"time": ts.isoformat(), "equity": f"{float(equity_value):.8f}", "context": context or ""}
    _write_csv_row(EQUITY_CSV, header, row)
