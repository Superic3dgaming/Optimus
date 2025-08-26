import pandas as pd
from datetime import datetime, timedelta, timezone

class MockDataFeed:
    def get_option_ohlcv(self, symbol, timeframe, start, end):
        # simple synthetic candles
        idx = pd.date_range(pd.to_datetime(start), pd.to_datetime(end), freq="15min", tz=timezone.utc)
        return pd.DataFrame({"open":1,"high":1.1,"low":0.9,"close":1.0}, index=idx)

    get_perp_ohlcv = get_option_ohlcv
