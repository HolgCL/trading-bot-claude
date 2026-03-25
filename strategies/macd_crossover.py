import pandas as pd

from strategies.base import Strategy, Signal


class MACDCrossoverStrategy(Strategy):
    """
    MACD line crossover strategy:
    - BUY when MACD line crosses above the signal line (bullish momentum)
    - SELL when MACD line crosses below the signal line (bearish momentum)
    - Optional: only trade when histogram changes sign (stricter entry)
    """

    name = "MACD Crossover"
    description = "Buy on bullish MACD crossover, sell on bearish crossover"

    def __init__(
        self,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ):
        super().__init__()
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        macd = self.indicators.macd(fast=self.fast, slow=self.slow, signal=self.signal)
        macd_line = macd["macd"]
        signal_line = macd["signal"]

        signals = pd.Series(Signal.HOLD, index=df.index, dtype=object)

        # Crossover: macd crosses above signal → BUY
        crossed_up = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
        # Crossunder: macd crosses below signal → SELL
        crossed_down = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))

        signals[crossed_up] = Signal.BUY
        signals[crossed_down] = Signal.SELL
        return signals
