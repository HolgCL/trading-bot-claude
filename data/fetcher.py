import os
import tempfile

import ccxt
import pandas as pd
import yfinance as yf
from datetime import datetime

from data.cache import CacheManager
from data.schema import OHLCV_COLUMNS

_DEFAULT_CACHE_DIR = os.path.join(tempfile.gettempdir(), "trading_bot_cache")

# Yahoo Finance works everywhere (no geo-restrictions, no AWS blocks).
# ccxt exchanges (Binance, Bybit, OKX) are blocked on Streamlit Cloud / AWS IPs.
SUPPORTED_EXCHANGES = {
    "yahoo":   "Yahoo Finance ✓ (works on cloud, recommended)",
    "bybit":   "Bybit (blocked on Streamlit Cloud / AWS)",
    "binance": "Binance (blocked on Streamlit Cloud / US IPs)",
    "okx":     "OKX (may be blocked on cloud)",
    "kraken":  "Kraken (may be blocked on cloud)",
}

# yfinance interval mapping from app timeframe format
_YF_INTERVAL_MAP = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "2h": "1h",  # yfinance has no 2h, use 1h
    "4h": "1h",              # yfinance has no 4h, use 1h and resample below
    "6h": "1h",
    "8h": "1h",
    "12h": "1h",
    "1d": "1d", "3d": "1d",
    "1w": "1wk",
    "1M": "1mo",
}

# Resample rules for timeframes yfinance doesn't natively support
_RESAMPLE_MAP = {
    "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h", "3d": "3d",
}


def _symbol_to_yf(symbol: str) -> str:
    """Convert 'BTC/USDT' → 'BTC-USD', 'ETH/BTC' → 'ETH-BTC'."""
    base, quote = symbol.split("/")
    # Yahoo Finance uses USD for USDT pairs
    if quote == "USDT":
        quote = "USD"
    return f"{base}-{quote}"


def _fetch_yahoo(symbol: str, timeframe: str, start: datetime, end: datetime) -> pd.DataFrame:
    yf_symbol = _symbol_to_yf(symbol)
    yf_interval = _YF_INTERVAL_MAP.get(timeframe, "1d")

    raw = yf.download(
        yf_symbol,
        start=start,
        end=end,
        interval=yf_interval,
        progress=False,
        auto_adjust=True,
    )

    if raw.empty:
        raise ValueError(f"No data returned from Yahoo Finance for {yf_symbol}")

    # Flatten MultiIndex columns if present (yfinance >= 0.2.x)
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    df = pd.DataFrame({
        "open":   raw["Open"],
        "high":   raw["High"],
        "low":    raw["Low"],
        "close":  raw["Close"],
        "volume": raw["Volume"],
    })
    df.index = pd.to_datetime(df.index, utc=True)
    df.index.name = "timestamp"

    # Resample if yfinance doesn't have the exact timeframe
    if timeframe in _RESAMPLE_MAP:
        rule = _RESAMPLE_MAP[timeframe]
        df = df.resample(rule).agg({
            "open": "first", "high": "max", "low": "min",
            "close": "last", "volume": "sum",
        }).dropna()

    return df.astype(float)


def _build_ccxt_exchange(exchange_id: str, api_key: str = "", api_secret: str = "") -> ccxt.Exchange:
    params = {"enableRateLimit": True, "options": {"defaultType": "spot"}}
    if api_key:
        params["apiKey"] = api_key
        params["secret"] = api_secret
    return getattr(ccxt, exchange_id)(params)


class DataFetcher:
    """
    Fetches historical OHLCV candles with local parquet cache.
    Default source is Yahoo Finance (works on Streamlit Cloud and all platforms).
    ccxt exchanges (Binance, Bybit, OKX) require direct internet access without
    AWS/cloud IP blocks.
    """

    def __init__(
        self,
        exchange_id: str = "yahoo",
        api_key: str = "",
        api_secret: str = "",
        cache_dir: str | None = None,
    ):
        self._exchange_id = exchange_id
        self._api_key = api_key
        self._api_secret = api_secret
        self._cache = CacheManager(cache_dir or _DEFAULT_CACHE_DIR)
        self._ccxt_exchange = None  # lazy init for ccxt

    def fetch(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        cache_key = self._cache.make_key(
            f"{self._exchange_id}_{symbol.replace('/', '_')}", timeframe, start, end
        )

        if not force_refresh and self._cache.exists(cache_key):
            return self._cache.load(cache_key)

        if self._exchange_id == "yahoo":
            df = _fetch_yahoo(symbol, timeframe, start, end)
        else:
            df = self._fetch_ccxt(symbol, timeframe, start, end)

        self._cache.save(cache_key, df)
        return df

    def _fetch_ccxt(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> pd.DataFrame:
        if self._ccxt_exchange is None:
            self._ccxt_exchange = _build_ccxt_exchange(
                self._exchange_id, self._api_key, self._api_secret
            )
        since_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)
        all_rows = []
        while since_ms < end_ms:
            batch = self._ccxt_exchange.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=1000)
            if not batch:
                break
            all_rows.extend(batch)
            since_ms = batch[-1][0] + 1
        df = pd.DataFrame(all_rows, columns=OHLCV_COLUMNS)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df = df.set_index("timestamp")
        df = df[df.index <= pd.Timestamp(end, tz="UTC")]
        return df.astype(float)

    def available_timeframes(self) -> list[str]:
        if self._exchange_id == "yahoo":
            return list(_YF_INTERVAL_MAP.keys())
        if self._ccxt_exchange is None:
            self._ccxt_exchange = _build_ccxt_exchange(self._exchange_id)
        return list(self._ccxt_exchange.timeframes.keys())
