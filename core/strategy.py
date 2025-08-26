from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class Signal:
    side: str   # 'BUY_CALL' / 'BUY_PUT' / etc.
    reason: str

class OptimusStrategy:
    def __init__(self, ema_period=20, rsi_period=14, rsi_buy=35, rsi_sell=65, sl_pct=0.003, tp_pct=0.006):
        self.ema_period = ema_period
        self.rsi_period = rsi_period
        self.rsi_buy = rsi_buy
        self.rsi_sell = rsi_sell
        self.sl_pct = sl_pct
        self.tp_pct = tp_pct

    def generate_signal(self, price: float, time: datetime) -> Optional[Signal]:
        # Toy rule: alternate between BUY_CALL and BUY_PUT to exercise pipeline
        if int(time.timestamp()) % 2 == 0:
            return Signal(side="BUY_CALL", reason="even-tick")
        else:
            return Signal(side="BUY_PUT", reason="odd-tick")

    def execute_signal(self, signal: Signal, price: float, time: datetime, mode: str):
        qty = 1_000  # placeholder sizing
        trade = {
            "time": str(time), "side": "CALL" if "CALL" in signal.side else "PUT",
            "signal": signal.side, "qty": qty, "entry_price": price,
            "sl_price": price*(1-self.sl_pct), "tp_price": price*(1+self.tp_pct),
            "exit_time": str(time), "exit_price": price, "pnl": 0.0,
            "outcome": "SIM", "status": "CLOSED", "mode": mode
        }
        return trade
