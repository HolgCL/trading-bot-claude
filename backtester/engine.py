from __future__ import annotations

import pandas as pd
from dataclasses import dataclass

from strategies.base import Strategy, Signal
from backtester.portfolio import Portfolio
from backtester.metrics import MetricsCalculator
from indicators.registry import IndicatorLibrary

# Candles per year for Sharpe/Sortino annualisation
_CANDLES_PER_YEAR = {
    "1m": 365 * 24 * 60,
    "5m": 365 * 24 * 12,
    "15m": 365 * 24 * 4,
    "30m": 365 * 24 * 2,
    "1h": 365 * 24,
    "2h": 365 * 12,
    "4h": 365 * 6,
    "6h": 365 * 4,
    "8h": 365 * 3,
    "12h": 365 * 2,
    "1d": 365,
    "3d": 365 // 3,
    "1w": 52,
    "1M": 12,
}


@dataclass
class BacktestConfig:
    initial_capital: float = 10_000.0
    commission_rate: float = 0.001   # 0.1% per trade (Binance spot standard)
    signal_fraction: float = 1.0    # fraction of cash to deploy on each BUY
    timeframe: str = "1h"           # used for correct Sharpe annualisation


@dataclass
class BacktestResult:
    equity_df: pd.DataFrame    # index=timestamp, columns=[equity]
    trades_df: pd.DataFrame    # one row per completed round-trip trade
    signals_df: pd.DataFrame   # index=timestamp, columns=[close, signal]
    metrics: dict
    orders: list
    config: BacktestConfig


class Backtester:
    """
    Orchestrates a full backtest:
    1. Injects IndicatorLibrary into strategy
    2. Calls strategy.generate_signals() to get BUY/SELL/HOLD for every bar
    3. Simulates execution: signal on bar[i] → execute on open of bar[i+1]
    4. Computes performance metrics
    """

    def __init__(self, config: BacktestConfig | None = None):
        self.config = config or BacktestConfig()

    def run(self, df: pd.DataFrame, strategy: Strategy) -> BacktestResult:
        library = IndicatorLibrary(df)
        strategy._inject_indicators(library)

        signals: pd.Series = strategy.generate_signals(df)

        portfolio = Portfolio(self.config.initial_capital, self.config.commission_rate)
        self._simulate(df, signals, portfolio)

        equity_df = portfolio.to_equity_df()
        trades_df = self._trades_to_df(portfolio.trades)

        candles_per_year = _CANDLES_PER_YEAR.get(self.config.timeframe, 365 * 24)
        metrics = MetricsCalculator.compute(
            equity_df, trades_df, self.config.initial_capital, candles_per_year
        )

        signals_df = pd.DataFrame({"close": df["close"], "signal": signals})

        return BacktestResult(
            equity_df=equity_df,
            trades_df=trades_df,
            signals_df=signals_df,
            metrics=metrics,
            orders=portfolio.orders,
            config=self.config,
        )

    def _simulate(self, df: pd.DataFrame, signals: pd.Series, portfolio: Portfolio) -> None:
        prices = df["close"].values
        opens = df["open"].values
        index = df.index

        for i in range(len(df) - 1):
            current_price = prices[i]
            next_open = opens[i + 1]
            signal = signals.iloc[i]

            portfolio.record_equity(index[i], current_price)

            if signal == Signal.BUY and not portfolio.position.is_open:
                portfolio.execute_buy(index[i + 1], next_open, self.config.signal_fraction)
            elif signal == Signal.SELL and portfolio.position.is_open:
                portfolio.execute_sell(index[i + 1], next_open)

        # Final bar: record equity and close any open position at last close
        portfolio.record_equity(index[-1], prices[-1])
        if portfolio.position.is_open:
            portfolio.execute_sell(index[-1], prices[-1])

    @staticmethod
    def _trades_to_df(trades) -> pd.DataFrame:
        if not trades:
            return pd.DataFrame(columns=[
                "entry_time", "exit_time", "entry_price",
                "exit_price", "quantity", "pnl", "pnl_pct", "direction",
            ])
        return pd.DataFrame([t.__dict__ for t in trades])
