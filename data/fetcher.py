import os
import tempfile

import ccxt
import pandas as pd
from datetime import datetime

from data.cache import CacheManager
from data.schema import OHLCV_COLUMNS

# Use /tmp on cloud (ephemeral) or local cache/ in dev
_DEFAULT_CACHE_DIR = os.path.join(tempfile.gettempdir(), "trading_bot_cache")

# Exchanges available in the UI. Bybit is default — no geo-restrictions.
# Binance is blocked from US IPs (Streamlit Cloud servers).
SUPPORTED_EXCHANGES = {
    "bybit":   "Bybit (recommended, global access)",
    "binance": "Binance (blocked on Streamlit Cloud / US IPs)",
    "okx":     "OKX (global access)",
    "kraken":  "Kraken (global access)",
}


def _build_exchange(exchange_id: str, api_key: str = "", api_secret: str = "") -> ccxt.Exchange:
    params = {"enableRateLimit": True}
    if api_key:
        params["apiKey"] = api_key
        params["secret"] = api_secret
    if exchange_id == "bybit":
        params["options"] = {"defaultType": "spot"}
    elif exchange_id == "binance":
        params["options"] = {"defaultType": "spot"}
    return getattr(ccxt, exchange_id)(params)


class DataFetcher:
    """Fetches historical OHLCV candles from a ccxt-supported exchange with parquet cache."""

    def __init__(
        self,
        exchange_id: str = "bybit",
        api_key: str = "",
        api_secret: str = "",
        cache_dir: str | None = None,
    ):
        self._exchange = _build_exchange(exchange_id, api_key, api_secret)
        self._exchange_id = exchange_id
        self._cache = CacheManager(cache_dir or _DEFAULT_CACHE_DIR)

    def fetch(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """
        Returns DataFrame with DatetimeTzDtype index (UTC) and OHLCV columns.
        Checks local parquet cache first; fetches from exchange on miss.
        """
        cache_key = self._cache.make_key(
            f"{self._exchange_id}_{symbol}", timeframe, start, end
        )

        if not force_refresh and self._cache.exists(cache_key):
            return self._cache.load(cache_key)

        df = self._fetch_from_exchange(symbol, timeframe, start, end)
        self._cache.save(cache_key, df)
        return df

    def _fetch_from_exchange(
        self, symbol: str, timeframe: str, start: datetime, end: datetime
    ) -> pd.DataFrame:
        since_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)
        all_rows = []

        while since_ms < end_ms:
            batch = self._exchange.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=1000)
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
        return list(self._exchange.timeframes.keys())

    def available_symbols(self, quote: str = "USDT") -> list[str]:
        markets = self._exchange.load_markets()
        return sorted(s for s in markets if s.endswith(f"/{quote}"))
