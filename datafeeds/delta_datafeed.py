import os
import requests
import pandas as pd
from core.http import HttpClient


class DeltaDataFeed:
    """
    DataFeed client for Delta Exchange
    """

    def __init__(self, base_url="https://api.delta.exchange", autodiscover=True, debug=True):
        self.base_url = base_url.rstrip("/")
        self.http = HttpClient()
        self.debug = debug
        self._products_cache = None

        if autodiscover:
            self._load_products()

    # -------------------------------
    # Internal helpers
    # -------------------------------
    def _get(self, path: str, params=None, attempts=3):
        url = f"{self.base_url}{path}"
        if self.debug:
            print(f"[DEBUG] GET {url} params={params}")
        r = self.http.get(url, params=params or {}, attempts=attempts)
        return r.json()

    def _load_products(self):
        """
        Cache product list from Delta.
        """
        if self._products_cache is not None:
            return self._products_cache

        data = self._get("/v2/products", {"limit": 10000})
        products = data.get("result", [])
        if self.debug:
            print(f"[DEBUG] Loaded {len(products)} products from Delta")

        self._products_cache = products
        return products

    # -------------------------------
    # Public API
    # -------------------------------
    def pick_option_instrument(self, config) -> str:
        """
        Auto-select an ETH option contract (nearest expiry + first strike).
        """
        root = config.get("root_symbol", "ETH")
        products = self._load_products()

        candidates = [p for p in products if p["symbol"].startswith(("C-", "P-")) and root in p["symbol"]]

        if self.debug:
            print(f"[DEBUG] Found {len(candidates)} option candidates for {root}")
            for p in candidates[:10]:
                print(f" - {p['symbol']} (id={p['id']})")

        if not candidates:
            raise RuntimeError(f"No option products found for {root}")

        chosen = candidates[0]  # TODO: refine to ATM/nearest expiry
        if self.debug:
            print(f"[DEBUG] Auto-selected option {chosen['symbol']} (id={chosen['id']})")
        return chosen["symbol"]

    def get_option_ohlcv(self, symbol: str, timeframe: str, start: str, end: str) -> pd.DataFrame:
        return self._fetch_candles(symbol, timeframe, start, end)

    def get_perp_ohlcv(self, symbol: str, timeframe: str, start: str, end: str) -> pd.DataFrame:
        return self._fetch_candles(symbol, timeframe, start, end)

    # -------------------------------
    # Candle fetching
    # -------------------------------
    def _fetch_candles(self, symbol: str, timeframe: str, start: str, end: str) -> pd.DataFrame:
        tf_map = {"15min": "15m", "15m": "15m", "1h": "1h", "1hr": "1h"}
        interval = tf_map.get(timeframe.lower(), "15m")

        if symbol.startswith(("C-ETH", "P-ETH")):  # option instrument
            path = "/v2/option-chain/candles"
        else:  # futures or perp
            path = "/v2/candles"

        params = {
            "resolution": interval,
            "start": start,
            "end": end,
        }

        if isinstance(symbol, str) and (symbol.startswith("C-") or symbol.startswith("P-")):
            # Option contract → must resolve to product_id
            products = self._load_products()
            match = next((p for p in products if p["symbol"] == symbol), None)
            if not match:
                raise RuntimeError(f"Unknown option symbol: {symbol}")
            params["product_id"] = match["id"]
        else:
            # Spot or perp
            params["symbol"] = symbol if isinstance(symbol, str) else str(symbol)

        data = self._get(path, params=params)
        candles = data.get("result", [])

        if not candles:
            raise RuntimeError(f"No candles returned for {symbol}")

        return pd.DataFrame(candles)
