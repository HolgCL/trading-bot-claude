from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

import pandas as pd


class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Strategy(ABC):
    """
    Base class for all trading strategies.

    Subclass this, implement `generate_signals`, and use `self.indicators`
    to access technical indicators. The backtester injects the indicator
    library before calling generate_signals.

    Example:
        class MyStrategy(Strategy):
            name = "RSI Strategy"

            def __init__(self, rsi_period=14, oversold=30, overbought=70):
                super().__init__()
                self.rsi_period = rsi_period
                self.oversold = oversold
                self.overbought = overbought

            def generate_signals(self, df):
                rsi = self.indicators.rsi(period=self.rsi_period)
                signals = pd.Series(Signal.HOLD, index=df.index)
                signals[rsi < self.oversold] = Signal.BUY
                signals[rsi > self.overbought] = Signal.SELL
                return signals
    """

    name: str = "Unnamed Strategy"
    description: str = ""

    def __init__(self):
        from indicators.registry import IndicatorLibrary
        self.indicators: IndicatorLibrary | None = None

    def _inject_indicators(self, library) -> None:
        """Called by Backtester before generate_signals. Do not override."""
        self.indicators = library

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Compute a signal for every bar in df.

        Args:
            df: OHLCV DataFrame (DatetimeTzDtype UTC index, float columns)

        Returns:
            pd.Series of Signal values (BUY / SELL / HOLD), same index as df.
            Signal on bar[i] is executed on the open of bar[i+1].
        """
        ...

    def get_params(self) -> dict:
        """Returns strategy parameters for display / Streamlit sliders."""
        return {
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith("_") and k != "indicators"
        }
