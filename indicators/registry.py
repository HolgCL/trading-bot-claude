import pandas as pd

from indicators.base import BaseIndicator
from indicators.technical import RSI, MACD, BollingerBands, SMA, EMA, OBV, VWAP


class IndicatorLibrary:
    """
    Accessor object injected into Strategy instances as `self.indicators`.
    Provides named methods for each built-in indicator with in-run caching.

    Usage inside a strategy:
        rsi     = self.indicators.rsi(period=14)          # pd.Series
        macd    = self.indicators.macd(fast=12, slow=26)  # pd.DataFrame
        bbands  = self.indicators.bbands()                # pd.DataFrame
        sma50   = self.indicators.sma(period=50)          # pd.Series
        custom  = self.indicators.custom("my_ml_model")   # pd.Series
    """

    def __init__(self, df: pd.DataFrame):
        self._df = df
        self._cache: dict[str, "pd.Series | pd.DataFrame"] = {}
        self._registry: dict[str, BaseIndicator] = {
            ind.name: ind for ind in [RSI(), MACD(), BollingerBands(), SMA(), EMA(), OBV(), VWAP()]
        }

    def _get(self, name: str, **kwargs):
        cache_key = f"{name}_{sorted(kwargs.items())}"
        if cache_key not in self._cache:
            self._cache[cache_key] = self._registry[name].compute(self._df, **kwargs)
        return self._cache[cache_key]

    # --- Built-in indicators ---

    def rsi(self, period: int = 14) -> pd.Series:
        return self._get("rsi", period=period)

    def macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        return self._get("macd", fast=fast, slow=slow, signal=signal)

    def bbands(self, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        return self._get("bbands", period=period, std_dev=std_dev)

    def sma(self, period: int = 20) -> pd.Series:
        return self._get("sma", period=period)

    def ema(self, period: int = 20) -> pd.Series:
        return self._get("ema", period=period)

    def obv(self) -> pd.Series:
        return self._get("obv")

    def vwap(self, period: int = 14) -> pd.Series:
        return self._get("vwap", period=period)

    # --- Custom / ML indicators ---

    def register(self, indicator: BaseIndicator) -> None:
        """Register a custom indicator (e.g. an ML model) by name."""
        self._registry[indicator.name] = indicator

    def custom(self, name: str, **kwargs):
        """Call a registered custom indicator by name."""
        if name not in self._registry:
            raise KeyError(f"Indicator '{name}' is not registered. Call library.register() first.")
        return self._get(name, **kwargs)
