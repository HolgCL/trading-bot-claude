import pandas as pd

from strategies.base import Strategy, Signal


class KeltnerMACDStrategy(Strategy):
    """
    Keltner Channel + MACD confluence strategy.

    Entry (BUY):
      - Цена закрылась ниже нижней полосы Кельтнера (перепроданность/откат)
      - MACD гистограмма разворачивается вверх (histogram[i] > histogram[i-1])
      → Ждём возврата цены к средней линии канала

    Exit (SELL):
      - Цена достигла средней линии канала (EMA), ИЛИ
      - Цена вышла за верхнюю полосу (взятие прибыли), ИЛИ
      - MACD гистограмма разворачивается вниз после роста

    Параметры:
        kc_period    : период EMA для канала (default 20)
        kc_multiplier: множитель ATR для ширины канала (default 2.25)
        macd_fast    : быстрый период MACD (default 12)
        macd_slow    : медленный период MACD (default 26)
        macd_signal  : сигнальный период MACD (default 9)
        exit_at_mid  : выходить на средней линии (True) или верхней полосе (False)
    """

    name = "Keltner Channel + MACD"
    description = (
        "Buy on a pullback to the lower Keltner band when the MACD turns up."
        "Exit on the middle line or top lane."
    )

    def __init__(
        self,
        kc_period: int = 20,
        kc_multiplier: float = 2.25,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        exit_at_mid: bool = True,
    ):
        super().__init__()
        self.kc_period = kc_period
        self.kc_multiplier = kc_multiplier
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.exit_at_mid = exit_at_mid

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        kc = self.indicators.keltner(
            period=self.kc_period, multiplier=self.kc_multiplier
        )
        macd = self.indicators.macd(
            fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal
        )

        hist = macd["histogram"]
        hist_turning_up = hist > hist.shift(1)   # гистограмма растёт
        hist_turning_down = hist < hist.shift(1) # гистограмма падает

        close = df["close"]

        # BUY: цена под нижней полосой И MACD разворачивается вверх
        buy_condition = (close < kc["lower"]) & hist_turning_up

        # SELL: цена достигла цели (mid или upper) ИЛИ MACD разворачивается вниз
        if self.exit_at_mid:
            price_target = close >= kc["mid"]
        else:
            price_target = close >= kc["upper"]

        sell_condition = price_target | ((close > kc["lower"]) & hist_turning_down & (hist < 0))

        signals = pd.Series(Signal.HOLD, index=df.index, dtype=object)
        signals[buy_condition] = Signal.BUY
        signals[sell_condition] = Signal.SELL
        return signals
