import pandas as pd
import ta.momentum as tm
import ta.trend as tt
import ta.volatility as tv
import ta.volume as tvo

from indicators.base import BaseIndicator


class RSI(BaseIndicator):
    name = "rsi"

    def compute(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        return tm.RSIIndicator(close=df["close"], window=period).rsi().rename("rsi")


class MACD(BaseIndicator):
    name = "macd"

    def compute(
        self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> pd.DataFrame:
        ind = tt.MACD(close=df["close"], window_slow=slow, window_fast=fast, window_sign=signal)
        return pd.DataFrame({
            "macd": ind.macd(),
            "signal": ind.macd_signal(),
            "histogram": ind.macd_diff(),
        }, index=df.index)


class BollingerBands(BaseIndicator):
    name = "bbands"

    def compute(
        self, df: pd.DataFrame, period: int = 20, std_dev: float = 2.0
    ) -> pd.DataFrame:
        ind = tv.BollingerBands(close=df["close"], window=period, window_dev=std_dev)
        return pd.DataFrame({
            "lower": ind.bollinger_lband(),
            "mid": ind.bollinger_mavg(),
            "upper": ind.bollinger_hband(),
        }, index=df.index)


class SMA(BaseIndicator):
    name = "sma"

    def compute(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        return tt.SMAIndicator(close=df["close"], window=period).sma_indicator().rename(f"sma_{period}")


class EMA(BaseIndicator):
    name = "ema"

    def compute(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        return tt.EMAIndicator(close=df["close"], window=period).ema_indicator().rename(f"ema_{period}")


class OBV(BaseIndicator):
    name = "obv"

    def compute(self, df: pd.DataFrame) -> pd.Series:
        return tvo.OnBalanceVolumeIndicator(
            close=df["close"], volume=df["volume"]
        ).on_balance_volume().rename("obv")


class VWAP(BaseIndicator):
    """Rolling VWAP over a configurable window."""
    name = "vwap"

    def compute(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        return tvo.VolumeWeightedAveragePrice(
            high=df["high"], low=df["low"], close=df["close"],
            volume=df["volume"], window=period,
        ).volume_weighted_average_price().rename("vwap")


class KeltnerChannel(BaseIndicator):
    """
    Keltner Channel: EMA of close ± multiplier * ATR.
    BUY signal when price breaks above upper band (momentum),
    or mean-reversion when price drops below lower band.
    """
    name = "keltner"

    def compute(
        self,
        df: pd.DataFrame,
        period: int = 20,
        multiplier: float = 2.25,
        original_version: bool = False,
    ) -> pd.DataFrame:
        ind = tv.KeltnerChannel(
            high=df["high"], low=df["low"], close=df["close"],
            window=period, multiplier=multiplier,
            original_version=original_version,
        )
        return pd.DataFrame({
            "lower": ind.keltner_channel_lband(),
            "mid":   ind.keltner_channel_mband(),
            "upper": ind.keltner_channel_hband(),
        }, index=df.index)
