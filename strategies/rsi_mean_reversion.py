import pandas as pd

from strategies.base import Strategy, Signal


class RSIMeanReversionStrategy(Strategy):
    """
    RSI mean reversion:
    - BUY when RSI drops below `oversold` (price likely to bounce)
    - SELL when RSI rises above `overbought` (price likely to drop)
    - Optional SMA trend filter: only buy when price is above SMA
    """

    name = "RSI Mean Reversion"
    description = "Buy oversold, sell overbought with optional SMA trend filter"

    def __init__(
        self,
        rsi_period: int = 14,
        oversold: float = 30.0,
        overbought: float = 70.0,
        sma_filter: bool = True,
        sma_period: int = 50,
    ):
        super().__init__()
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.sma_filter = sma_filter
        self.sma_period = sma_period

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        rsi = self.indicators.rsi(period=self.rsi_period)
        signals = pd.Series(Signal.HOLD, index=df.index, dtype=object)

        if self.sma_filter:
            sma = self.indicators.sma(period=self.sma_period)
            above_sma = df["close"] > sma
            signals[(rsi < self.oversold) & above_sma] = Signal.BUY
        else:
            signals[rsi < self.oversold] = Signal.BUY

        signals[rsi > self.overbought] = Signal.SELL
        return signals
