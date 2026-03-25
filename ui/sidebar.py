from __future__ import annotations

from datetime import datetime, date, timedelta

import streamlit as st

from backtester.engine import BacktestConfig
from strategies.rsi_mean_reversion import RSIMeanReversionStrategy
from strategies.macd_crossover import MACDCrossoverStrategy
from strategies.keltner_macd import KeltnerMACDStrategy

STRATEGY_MAP = {
    RSIMeanReversionStrategy.name: RSIMeanReversionStrategy,
    MACDCrossoverStrategy.name: MACDCrossoverStrategy,
    KeltnerMACDStrategy.name: KeltnerMACDStrategy,
}

TIMEFRAME_OPTIONS = ["1h", "4h", "1d", "15m", "30m", "2h", "6h", "12h"]


def render_sidebar():
    """
    Renders all sidebar controls and returns (config, strategy, df).
    Data is fetched here so the user sees a spinner in the sidebar.
    """
    st.sidebar.header("Backtest Settings")

    # Symbol
    symbol = st.sidebar.text_input("Symbol", value="BTC/USDT")

    # Timeframe
    timeframe = st.sidebar.selectbox("Timeframe", TIMEFRAME_OPTIONS, index=0)

    # Date range
    default_end = date.today()
    default_start = default_end - timedelta(days=365)
    start_date = st.sidebar.date_input("Start Date", value=default_start)
    end_date = st.sidebar.date_input("End Date", value=default_end)

    st.sidebar.divider()

    # Strategy selection
    strategy_name = st.sidebar.selectbox("Strategy", list(STRATEGY_MAP.keys()))
    strategy_cls = STRATEGY_MAP[strategy_name]

    st.sidebar.markdown(f"*{strategy_cls.description}*")
    st.sidebar.divider()

    # Strategy-specific parameters
    strategy = _build_strategy(strategy_cls)

    st.sidebar.divider()

    # Backtest config
    st.sidebar.subheader("Portfolio Settings")
    initial_capital = st.sidebar.number_input(
        "Initial Capital (USDT)", min_value=100.0, value=10_000.0, step=100.0
    )
    commission_pct = st.sidebar.slider(
        "Commission %", min_value=0.0, max_value=0.5, value=0.1, step=0.01
    )
    signal_fraction = st.sidebar.slider(
        "Position Size (% of cash)", min_value=10, max_value=100, value=100, step=5
    ) / 100.0

    config = BacktestConfig(
        initial_capital=initial_capital,
        commission_rate=commission_pct / 100,
        signal_fraction=signal_fraction,
        timeframe=timeframe,
    )

    # Fetch data
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.min.time())

    return config, strategy, symbol, timeframe, start_dt, end_dt


def _build_strategy(strategy_cls):
    """Render parameter sliders specific to each strategy and return an instance."""
    if strategy_cls is RSIMeanReversionStrategy:
        rsi_period = st.sidebar.slider("RSI Period", 5, 50, 14)
        oversold = st.sidebar.slider("Oversold Level", 10, 45, 30)
        overbought = st.sidebar.slider("Overbought Level", 55, 90, 70)
        sma_filter = st.sidebar.checkbox("SMA Trend Filter", value=True)
        sma_period = st.sidebar.slider("SMA Period", 10, 200, 50, disabled=not sma_filter)
        return RSIMeanReversionStrategy(
            rsi_period=rsi_period,
            oversold=float(oversold),
            overbought=float(overbought),
            sma_filter=sma_filter,
            sma_period=sma_period,
        )

    elif strategy_cls is MACDCrossoverStrategy:
        fast = st.sidebar.slider("Fast Period", 5, 30, 12)
        slow = st.sidebar.slider("Slow Period", 15, 60, 26)
        signal = st.sidebar.slider("Signal Period", 3, 20, 9)
        return MACDCrossoverStrategy(fast=fast, slow=slow, signal=signal)

    elif strategy_cls is KeltnerMACDStrategy:
        st.sidebar.markdown("**Keltner Channel**")
        kc_period = st.sidebar.slider("KC Period", 10, 50, 20)
        kc_multiplier = st.sidebar.slider("ATR Multiplier", 1.0, 4.0, 2.25, step=0.05)
        exit_at_mid = st.sidebar.radio(
            "Exit Target", ["Middle line (EMA)", "Upper band"],
            index=0,
        ) == "Middle line (EMA)"
        st.sidebar.markdown("**MACD**")
        macd_fast = st.sidebar.slider("MACD Fast", 5, 30, 12)
        macd_slow = st.sidebar.slider("MACD Slow", 15, 60, 26)
        macd_signal = st.sidebar.slider("MACD Signal", 3, 20, 9)
        return KeltnerMACDStrategy(
            kc_period=kc_period,
            kc_multiplier=kc_multiplier,
            macd_fast=macd_fast,
            macd_slow=macd_slow,
            macd_signal=macd_signal,
            exit_at_mid=exit_at_mid,
        )

    # Default: instantiate with no args
    return strategy_cls()
