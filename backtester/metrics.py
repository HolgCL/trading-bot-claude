import numpy as np
import pandas as pd


class MetricsCalculator:
    """Computes performance metrics from equity curve and trade list."""

    @classmethod
    def compute(
        cls,
        equity_df: pd.DataFrame,
        trades_df: pd.DataFrame,
        initial_capital: float,
        candles_per_year: float = 365 * 24,  # hourly by default; pass 365 for daily
    ) -> dict:
        equity = equity_df["equity"]
        total_return = (equity.iloc[-1] - initial_capital) / initial_capital
        returns = equity.pct_change().dropna()

        return {
            "Final Equity": round(equity.iloc[-1], 2),
            "Total P&L": round(equity.iloc[-1] - initial_capital, 2),
            "Total Return %": round(total_return * 100, 2),
            "Sharpe Ratio": round(cls._sharpe(returns, candles_per_year), 3),
            "Sortino Ratio": round(cls._sortino(returns, candles_per_year), 3),
            "Max Drawdown %": round(cls._max_drawdown(equity) * 100, 2),
            "Calmar Ratio": round(cls._calmar(total_return, cls._max_drawdown(equity)), 3),
            "Total Trades": len(trades_df) if not trades_df.empty else 0,
            "Win Rate %": round(cls._win_rate(trades_df), 2),
            "Avg Win %": round(cls._avg_win(trades_df), 2),
            "Avg Loss %": round(cls._avg_loss(trades_df), 2),
            "Profit Factor": round(cls._profit_factor(trades_df), 3),
            "Avg Trade Duration": cls._avg_duration(trades_df),
        }

    @staticmethod
    def _sharpe(returns: pd.Series, candles_per_year: float) -> float:
        if returns.std() == 0:
            return 0.0
        return float(returns.mean() / returns.std() * np.sqrt(candles_per_year))

    @staticmethod
    def _sortino(returns: pd.Series, candles_per_year: float) -> float:
        downside = returns[returns < 0]
        if len(downside) == 0 or downside.std() == 0:
            return 0.0
        return float(returns.mean() / downside.std() * np.sqrt(candles_per_year))

    @staticmethod
    def _max_drawdown(equity: pd.Series) -> float:
        peak = equity.cummax()
        drawdown = (equity - peak) / peak
        return float(drawdown.min())

    @staticmethod
    def _calmar(total_return: float, max_drawdown: float) -> float:
        if max_drawdown == 0:
            return 0.0
        return abs(total_return / max_drawdown)

    @staticmethod
    def _win_rate(trades_df: pd.DataFrame) -> float:
        if trades_df.empty:
            return 0.0
        return float((trades_df["pnl"] > 0).sum() / len(trades_df) * 100)

    @staticmethod
    def _avg_win(trades_df: pd.DataFrame) -> float:
        if trades_df.empty:
            return 0.0
        winners = trades_df[trades_df["pnl"] > 0]["pnl_pct"]
        return float(winners.mean() * 100) if not winners.empty else 0.0

    @staticmethod
    def _avg_loss(trades_df: pd.DataFrame) -> float:
        if trades_df.empty:
            return 0.0
        losers = trades_df[trades_df["pnl"] < 0]["pnl_pct"]
        return float(losers.mean() * 100) if not losers.empty else 0.0

    @staticmethod
    def _profit_factor(trades_df: pd.DataFrame) -> float:
        if trades_df.empty:
            return 0.0
        gross_profit = trades_df[trades_df["pnl"] > 0]["pnl"].sum()
        gross_loss = abs(trades_df[trades_df["pnl"] < 0]["pnl"].sum())
        return float(gross_profit / gross_loss) if gross_loss > 0 else float("inf")

    @staticmethod
    def _avg_duration(trades_df: pd.DataFrame) -> str:
        if trades_df.empty or "entry_time" not in trades_df.columns:
            return "N/A"
        durations = pd.to_datetime(trades_df["exit_time"]) - pd.to_datetime(trades_df["entry_time"])
        return str(durations.mean()).split(".")[0]
