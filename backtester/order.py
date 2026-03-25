from dataclasses import dataclass
from datetime import datetime


@dataclass
class Order:
    timestamp: datetime
    signal: str         # "BUY" | "SELL"
    price: float        # execution price (next bar open)
    quantity: float     # base asset units (e.g. BTC)
    commission: float   # absolute cost in quote currency
    portfolio_value: float


@dataclass
class Trade:
    """Completed round-trip trade (entry + exit)."""
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float          # absolute profit/loss in quote currency
    pnl_pct: float      # relative profit/loss (0.05 = 5%)
    direction: str      # "LONG"
