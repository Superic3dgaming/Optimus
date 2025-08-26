from __future__ import annotations
from datetime import datetime

class RiskManager:
    def __init__(self, max_position_notional: float, max_daily_loss: float, allow_both_sides: bool):
        self.max_position_notional = max_position_notional
        self.max_daily_loss = max_daily_loss
        self.allow_both_sides = allow_both_sides

    def can_trade(self, side: str, price: float, time: datetime) -> bool:
        return True  # simple stub, extend as needed
