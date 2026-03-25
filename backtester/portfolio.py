from __future__ import annotations

import pandas as pd
from dataclasses import dataclass, field

from backtester.order import Order, Trade


@dataclass
class Position:
    quantity: float = 0.0
    avg_price: float = 0.0
    entry_time: object = None

    @property
    def is_open(self) -> bool:
        return self.quantity > 0


class Portfolio:
    """
    Tracks cash, open position, order history, completed trades, and equity curve.
    Commission model: flat percentage of trade value (e.g. 0.001 = 0.1%).
    """

    def __init__(self, initial_capital: float, commission_rate: float = 0.001):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.cash = initial_capital
        self.position = Position()
        self.orders: list[Order] = []
        self.trades: list[Trade] = []
        self.equity_curve: list[tuple] = []

    def record_equity(self, timestamp, current_price: float) -> None:
        value = self.cash + self.position.quantity * current_price
        self.equity_curve.append((timestamp, value))

    def execute_buy(self, timestamp, price: float, fraction: float = 1.0) -> Order | None:
        """Buy using `fraction` of available cash (default: all-in)."""
        if self.cash <= 0:
            return None
        spend = self.cash * fraction
        commission = spend * self.commission_rate
        net_spend = spend - commission
        quantity = net_spend / price
        self.cash -= spend
        self._update_position(quantity, price, timestamp)
        order = Order(timestamp, "BUY", price, quantity, commission,
                      self.cash + quantity * price)
        self.orders.append(order)
        return order

    def execute_sell(self, timestamp, price: float) -> Order | None:
        """Sell entire position."""
        if not self.position.is_open:
            return None
        quantity = self.position.quantity
        gross = quantity * price
        commission = gross * self.commission_rate
        proceeds = gross - commission
        self.cash += proceeds
        cost_basis = quantity * self.position.avg_price
        pnl = proceeds - cost_basis
        pnl_pct = pnl / cost_basis if cost_basis > 0 else 0.0
        self.trades.append(Trade(
            self.position.entry_time, timestamp,
            self.position.avg_price, price,
            quantity, pnl, pnl_pct, "LONG",
        ))
        self._reset_position()
        order = Order(timestamp, "SELL", price, quantity, commission, self.cash)
        self.orders.append(order)
        return order

    def _update_position(self, quantity: float, price: float, timestamp) -> None:
        if not self.position.is_open:
            self.position.entry_time = timestamp
            self.position.avg_price = price
            self.position.quantity = quantity
        else:
            total_cost = self.position.quantity * self.position.avg_price + quantity * price
            self.position.quantity += quantity
            self.position.avg_price = total_cost / self.position.quantity

    def _reset_position(self) -> None:
        self.position = Position()

    def to_equity_df(self) -> pd.DataFrame:
        df = pd.DataFrame(self.equity_curve, columns=["timestamp", "equity"])
        return df.set_index("timestamp")
