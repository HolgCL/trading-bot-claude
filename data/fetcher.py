import ccxt
import pandas as pd
from datetime import datetime

from data.cache import CacheManager
from data.schema import OHLCV_COLUMNS


class DataFetcher:
    """Fetches historical OHLCV candles from Binance with local parquet cache."""

    def __init__(self, api_key: str = "", api_secret: str = "", cache_dir: str = "cache/"):
        self._exchange = ccxt.binance({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        })
        self._cache = CacheManager(cache_dir)

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
        Checks local parquet cache first; fetches from Binance on miss.
        """
        cache_key = self._cache.make_key(symbol, timeframe, start, end)

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
