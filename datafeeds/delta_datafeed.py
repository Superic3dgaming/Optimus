from __future__ import annotations
from typing import Optional, Dict, Any, Tuple, List
import os, json
from datetime import datetime, timezone, timedelta

import numpy as np
import pandas as pd

from core.http import ResilientHTTP

STATE_DIR = "state"
STATE_FILE = os.path.join(STATE_DIR, "auto_config.json")


def _save_state(d: dict) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)


def _infer_epoch_unit(x: float) -> str:
    try:
        xv = float(x)
    except Exception:
        return "s"
    return "ms" if xv > 1e12 else "s"


def _ensure_ohlc_indexed(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close"])

    out = df.copy()

    # rename to open/high/low/close if API uses different keys
    renames = [
        {"o": "open", "h": "high", "l": "low", "c": "close"},
        {"open_price": "open", "high_price": "high", "low_price": "low", "close_price": "close"},
        {"openPrice": "open", "highPrice": "high", "lowPrice": "low", "closePrice": "close"},
    ]
    for cmap in renames:
        hit = set(cmap.keys()) & set(out.columns)
        if hit:
            out = out.rename(columns=cmap)

    # find a timestamp column if present
    ts_col = next(
        (c for c in ["t", "time", "timestamp", "start_at", "date", "datetime", "start_time"] if c in out.columns),
        None
    )

    if ts_col is None:
        if not isinstance(out.index, pd.DatetimeIndex):
            out.index = pd.to_datetime(out.index, utc=True, errors="coerce")
    else:
        if np.issubdtype(out[ts_col].dtype, np.number):
            unit = _infer_epoch_unit(out[ts_col].iloc[0])
            out[ts_col] = pd.to_datetime(out[ts_col], unit=unit, utc=True, errors="coerce")
        else:
            out[ts_col] = pd.to_datetime(out[ts_col], utc=True, errors="coerce")
        out = out.set_index(ts_col).sort_index()

    for c in ["open", "high", "low", "close"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")

    return out[["open", "high", "low", "close"]].dropna()


class DeltaDataFeed:
    """
    Autonomous Delta public API adapter:
      - Can work discovery-free via env (product_id or symbol)
      - Or auto-pick the nearest-expiry ATM option for a given root (e.g., ETH)
    """

    CANDLE_PATHS = ["/v3/public/candles", "/v2/public/candles", "/public/candles"]
    # Product endpoints (drop deprecated /public/products)
    PRODUCT_PATHS = [
        "/v3/public/products",
        "/v2/public/products",
    ]

    INTERVAL_PARAMS = ["interval", "resolution", "granularity"]
    SYMBOL_PARAMS = ["product_id", "symbol", "instrument_name", "name"]

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 10,
        autodiscover: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.http = ResilientHTTP(timeout_connect=5.0, timeout_read=5.0, default_attempts=2)
        self._debug = os.getenv("OPTIMUS_DEBUG", "").lower() in ("1", "true", "yes")

        # Paths & params from env (with sensible defaults)
        self._candles_path = os.getenv("OPTIMUS_API_PATH_CANDLES") or "/v3/public/candles"
        self._products_path = os.getenv("OPTIMUS_API_PATH_PRODUCTS") or "/v3/public/products"
        self._interval_param = os.getenv("OPTIMUS_CANDLES_INTERVAL_PARAM") or "interval"
        self._symbol_param = os.getenv("OPTIMUS_CANDLES_SYMBOL_PARAM") or "product_id"
        self._start_param = os.getenv("OPTIMUS_CANDLES_START_PARAM") or "start_time"
        self._end_param = os.getenv("OPTIMUS_CANDLES_END_PARAM") or "end_time"

        # Market config
        self.underlying_symbol = os.getenv("OPTIMUS_UNDERLYING", "ETHUSD")
        self.option_root = os.getenv("OPTIMUS_OPTION_ROOT", "ETH")
        self.option_type_pref = os.getenv("OPTIMUS_OPTION_TYPE", "both").lower()  # "call" / "put" / "both"

        # Explicit override (discovery-free)
        self.explicit_opt_symbol = os.getenv("OPTIMUS_OPTION_SYMBOL") or ""
        self.explicit_opt_pid = os.getenv("OPTIMUS_OPTION_PRODUCT_ID") or ""
        self.explicit_perp_pid = os.getenv("OPTIMUS_PERP_PRODUCT_ID") or ""

        self.disable_discovery = os.getenv("OPTIMUS_DISABLE_DISCOVERY", "1").lower() in ("1", "true", "yes")
        self.autodetect_option = os.getenv("OPTIMUS_AUTO_SELECT", "1").lower() in ("1", "true", "yes")

    # ---------- HTTP helpers ----------
    def _headers(self) -> Dict[str, str]:
        return {"Content-Type": "application/json"}

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None, attempts: int = 1) -> Any:
        url = f"{self.base_url}{path}"
        if self._debug:
            print(f"[DEBUG] GET {url} params={params}")
        r = self.http.get(url, headers=self._headers(), params=params or {}, attempts=attempts)
        return r.json()

    # ---------- Candles ----------
    def get_option_ohlcv(self, symbol: str, timeframe: str, start: str, end: str) -> pd.DataFrame:
        return self._fetch_candles(symbol, timeframe, start, end)

    def get_perp_ohlcv(self, symbol: str, timeframe: str, start: str, end: str) -> pd.DataFrame:
        return self._fetch_candles(symbol, timeframe, start, end)
    
    def _fetch_candles(self, symbol: str, timeframe: str, start: str, end: str) -> pd.DataFrame:
        # Normalize timeframe
        tf_map = {
            "15min": "15m",
            "15m": "15m",
            "1h": "1h",
            "1hr": "1h",
        }
        interval = tf_map.get(timeframe.lower(), "15m")

        symbol_param = self._symbol_param
        value = symbol

        if symbol_param == "product_id":
            # Only treat exact underlying tickers as perps; NOT roots like "ETH" or "BTC"
            UNDERLYINGS = {"ETHUSD", "BTCUSD"}
            try:
                value = int(symbol)  # numeric product id is fine
            except Exception:
                if symbol.upper() in UNDERLYINGS:
                    if not self.explicit_perp_pid:
                        raise RuntimeError(
                            "Endpoint expects product_id but OPTIMUS_PERP_PRODUCT_ID is not set for underlying."
                        )
                    value = int(self.explicit_perp_pid)
                else:
                    # Option request must have an option product_id (auto-select or explicit)
                    if not self.explicit_opt_pid:
                        raise RuntimeError(
                            "Endpoint expects product_id for option candles, but no option product id is available. "
                            "Enable OPTIMUS_AUTO_SELECT=1 or set OPTIMUS_OPTION_PRODUCT_ID."
                        )
                    value = int(self.explicit_opt_pid)

        params = {
            self._interval_param: interval,
            symbol_param: value,
            "limit": 1000,
            self._start_param: start,
            self._end_param: end,
        }

        data = self._get(self._candles_path, params, attempts=1)

        payload = data if isinstance(data, list) else None
        if payload is None and isinstance(data, dict):
            for k in ("result", "data", "candles", "items"):
                if isinstance(data.get(k), list):
                    payload = data[k]
                    break

        df = pd.DataFrame(payload or [])
        return _ensure_ohlc_indexed(df)


    # ---------- Auto selection ----------
    def pick_option_instrument(self, config: dict, now_utc: Optional[datetime] = None) -> str:
        """
        Returns either a product_id (str) or a symbol (str), depending on OPTIMUS_CANDLES_SYMBOL_PARAM.
        Priority:
          1) Explicit overrides in .env (OPTIMUS_OPTION_SYMBOL / OPTIMUS_OPTION_PRODUCT_ID)
          2) If OPTIMUS_AUTO_SELECT=1, discover nearest expiry ATM option for option_root (e.g., ETH)
          3) Fallback: return option_root (some endpoints accept an index/root symbol)
        """
        # 1) Explicit overrides
        if self.explicit_opt_symbol:
            print(f"[INFO] Using OPTIMUS_OPTION_SYMBOL={self.explicit_opt_symbol}")
            return self.explicit_opt_symbol
        if self.explicit_opt_pid:
            int(self.explicit_opt_pid)  # validate numeric
            print(f"[INFO] Using OPTIMUS_OPTION_PRODUCT_ID={self.explicit_opt_pid} (bypassing product list)")
            return str(self.explicit_opt_pid)

        # 2) Auto-select if enabled
        if self.autodetect_option:
            try:
                pid = self._auto_select_option_pid(now_utc=now_utc)
                if pid is not None:
                    if self._symbol_param == "product_id":
                        return str(pid)
                    # if endpoint expects symbol, try to find the symbol from products list
                    sym = self._symbol_for_product_id(pid)
                    if sym:
                        return sym
                    # if symbol lookup failed, still return pid; _fetch_candles will adapt if using product_id param
                    return str(pid)
            except Exception as e:
                print(f"[WARN] Auto-select failed: {e}. Will fallback to root symbol.")

        # 3) Fallback: root (rarely accepted for options; mostly for indices)
        return self.option_root

    # ---------- Product catalog ----------
    def _load_products(self, limit: int = 10000) -> pd.DataFrame:
        """
        Try v3 then v2 products. Return a normalized DataFrame with fields we care about:
          product_id, symbol, product_type, underlying, option_type, strike_price, settle_time (UTC)
        """
        paths = [self._products_path] if self._products_path else []
        for p in self.PRODUCT_PATHS:
            if p not in paths:
                paths.append(p)

        last_err = None
        for path in paths:
            try:
                data = self._get(path, {"limit": limit}, attempts=1)
                items = data if isinstance(data, list) else data.get("result") or data.get("data") or data.get("products")
                if not isinstance(items, list):
                    continue
                df = pd.DataFrame(items)
                if df.empty:
                    continue
                # Normalize columns
                cols = df.columns
                # Commonly present:
                # - product_id (int)
                # - symbol (str) e.g., "ETH-29AUG24-2500-C"
                # - product_type e.g., "call_options"/"put_options"/"perpetual_futures"
                # Optional fields:
                # - underlying (e.g., "ETHUSD" or "ETH")
                # - option_type ("call"/"put")
                # - strike_price (float)
                # - settle_time / expiry datetime

                # Try to create normalized fields:
                df["product_id"] = pd.to_numeric(df.get("product_id"), errors="coerce")
                df["symbol"] = df.get("symbol")
                df["product_type"] = df.get("product_type") or df.get("type")

                # option_type
                if "option_type" not in df.columns:
                    # infer from product_type
                    df["option_type"] = np.where(df["product_type"].astype(str).str.contains("call", case=False), "call",
                                      np.where(df["product_type"].astype(str).str.contains("put", case=False), "put", None))

                # strike
                if "strike_price" not in df.columns:
                    df["strike_price"] = pd.to_numeric(df.get("strike") or df.get("strikePrice"), errors="coerce")

                # underlying
                if "underlying" not in df.columns:
                    df["underlying"] = df.get("underlying_symbol") or df.get("underlying_asset") or df.get("base_asset")

                # expiry
                expiry_col = None
                for c in ["settle_time", "expiry_time", "expiration_time", "expiry", "expiry_at"]:
                    if c in df.columns:
                        expiry_col = c; break
                if expiry_col:
                    # parse to UTC
                    df["expiry_dt"] = pd.to_datetime(df[expiry_col], utc=True, errors="coerce")
                else:
                    df["expiry_dt"] = pd.NaT

                # Keep only rows we understand
                keep_cols = ["product_id", "symbol", "product_type", "underlying", "option_type", "strike_price", "expiry_dt"]
                out = df[keep_cols].dropna(subset=["product_id", "symbol", "product_type"], how="any")
                return out
            except Exception as e:
                last_err = e
                continue

        if last_err:
            raise last_err
        raise RuntimeError("Failed to load products: no valid response from any products endpoint.")

    def _symbol_for_product_id(self, pid: int) -> Optional[str]:
        try:
            df = self._load_products()
        except Exception:
            return None
        row = df.loc[df["product_id"] == int(pid)]
        if not row.empty:
            return str(row.iloc[0]["symbol"])
        return None

    # ---------- Auto-picker ----------
    def _auto_select_option_pid(self, now_utc: Optional[datetime] = None) -> Optional[int]:
        """
        From the full products list:
          - Filter to options for the desired root (e.g., "ETH" or underlying "ETHUSD")
          - Select the nearest *future* expiry
          - Select strike closest to the latest underlying price
          - Honor OPTIMUS_OPTION_TYPE preference ("call", "put", "both")
        Returns product_id or None.
        """
        df = self._load_products()

        # Filter to options
        mask_opt = df["product_type"].astype(str).str.contains("options", case=False, na=False)
        df = df.loc[mask_opt].copy()
        if df.empty:
            raise RuntimeError("Products list contains no options.")

        # Filter to ETH-rooted contracts
        root = self.option_root.upper()
        underlying = self.underlying_symbol.upper()
        # Accept rows where symbol starts with root-  OR underlying mentions root
        df = df[(df["symbol"].astype(str).str.upper().str.startswith(root + "-")) |
                (df["underlying"].astype(str).str.upper().str.contains(root)) |
                (df["underlying"].astype(str).str.upper().str.contains(underlying))]
        if df.empty:
            raise RuntimeError(f"No options found for root={root} / underlying={underlying}.")

        # Future expiries only
        now = now_utc or datetime.now(timezone.utc)
        df = df[df["expiry_dt"].notna()]
        df = df[df["expiry_dt"] >= (now - timedelta(minutes=1))]
        if df.empty:
            raise RuntimeError("No future/active option expiries found.")

        # Get current underlying price
        spot = self._get_underlying_price()
        if not np.isfinite(spot) or spot <= 0:
            raise RuntimeError("Failed to obtain a valid underlying price for ATM selection.")

        # Keep preferred type
        pref = self.option_type_pref
        if pref in ("call", "put"):
            df = df[df["option_type"].astype(str).str.lower() == pref]
            if df.empty:
                raise RuntimeError(f"No {pref} options available for selection.")

        # Choose nearest expiry (min expiry_dt)
        df = df.sort_values(["expiry_dt"])
        nearest_expiry = df["expiry_dt"].iloc[0]
        cexp = df[df["expiry_dt"] == nearest_expiry].copy()
        if cexp.empty:
            return None

        # Choose ATM: closest strike to spot
        cexp["abs_d"] = (pd.to_numeric(cexp["strike_price"], errors="coerce") - spot).abs()
        cexp = cexp.sort_values(["abs_d"])
        best = cexp.iloc[0]
        pid = int(best["product_id"])
        print(f"[INFO] Auto-selected option: symbol={best['symbol']} pid={pid} expiry={nearest_expiry} strike={best['strike_price']}, spot≈{spot:.2f}")
        return pid

    # ---------- Underlying price ----------
    def _get_underlying_price(self) -> float:
        """
        Fetch a recent price for the underlying via candles (limit=1).
        If endpoint expects product_id, use OPTIMUS_PERP_PRODUCT_ID.
        Otherwise use symbol param with underlying ticker (e.g., ETHUSD).
        """
        path = self._candles_path or "/v3/public/candles"
        interval = "1h"
        start = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        symbol_param = self._symbol_param
        value: Any = self.underlying_symbol

        if symbol_param == "product_id":
            if not self.explicit_perp_pid:
                raise RuntimeError(
                    "OPTIMUS_CANDLES_SYMBOL_PARAM=product_id but OPTIMUS_PERP_PRODUCT_ID is not set"
                )
            value = int(self.explicit_perp_pid)

        params = {
            self._interval_param: "1h",
            symbol_param: value,
            "limit": 1,
            self._start_param: start,
            self._end_param: end,
        }

        data = self._get(path, params, attempts=1)
        payload = data if isinstance(data, list) else None
        if payload is None and isinstance(data, dict):
            for k in ("result", "data", "candles", "items"):
                if isinstance(data.get(k), list):
                    payload = data[k]
                    break

        df = _ensure_ohlc_indexed(pd.DataFrame(payload or []))
        if df.empty:
            raise RuntimeError("No candles returned for underlying price probe.")
        # last close as spot
        return float(df["close"].iloc[-1])

