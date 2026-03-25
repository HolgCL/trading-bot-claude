from abc import ABC, abstractmethod
import pandas as pd


class BaseIndicator(ABC):
    """
    Every indicator takes a price DataFrame and returns a Series or DataFrame.
    Indicators must be stateless — same input always yields same output.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier used in IndicatorLibrary registry."""
        ...

    @abstractmethod
    def compute(self, df: pd.DataFrame, **kwargs) -> "pd.Series | pd.DataFrame":
        """
        Args:
            df: OHLCV DataFrame (timestamp index, columns: open/high/low/close/volume)
            **kwargs: indicator-specific parameters

        Returns:
            pd.Series for single-value indicators (RSI → one series)
            pd.DataFrame for multi-value indicators (MACD → macd/signal/histogram)
        """
        ...
