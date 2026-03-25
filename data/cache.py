import pandas as pd
from pathlib import Path


class CacheManager:
    def __init__(self, cache_dir: str = "cache/"):
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def make_key(self, symbol: str, timeframe: str, start, end) -> str:
        raw = f"{symbol}_{timeframe}_{start.date()}_{end.date()}"
        return raw.replace("/", "_")

    def _path(self, key: str) -> Path:
        return self._dir / f"{key}.parquet"

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def load(self, key: str) -> pd.DataFrame:
        return pd.read_parquet(self._path(key))

    def save(self, key: str, df: pd.DataFrame) -> None:
        df.to_parquet(self._path(key), engine="pyarrow", compression="snappy")

    def list_cached(self) -> list[str]:
        return [p.stem for p in self._dir.glob("*.parquet")]

    def delete(self, key: str) -> None:
        p = self._path(key)
        if p.exists():
            p.unlink()
