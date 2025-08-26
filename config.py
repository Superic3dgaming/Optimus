import os

CONFIG = {
    "mode": os.getenv("OPTIMUS_MODE", "BACKTEST").upper(),
    "account": {
        "starting_equity": float(os.getenv("OPTIMUS_START_EQUITY", "10000"))
    },
    "market": {
        "perp_symbol": os.getenv("OPTIMUS_UNDERLYING", "ETHUSD"),
        "option_symbol_root": os.getenv("OPTIMUS_OPTION_ROOT", "ETH"),
        "instrument_query": {"option_type": os.getenv("OPTIMUS_OPTION_TYPE", "both")},
    },
    "api": {
        "base": os.getenv("OPTIMUS_API_BASE", "https://api.delta.exchange"),
        "candles": os.getenv("OPTIMUS_API_PATH_CANDLES"),
        "products": os.getenv("OPTIMUS_API_PATH_PRODUCTS"),
        "interval_param": os.getenv("OPTIMUS_CANDLES_INTERVAL_PARAM", "interval"),
        "symbol_param": os.getenv("OPTIMUS_CANDLES_SYMBOL_PARAM", "symbol"),
    },
}
