import sys
import os

# Allow imports from project root regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(
    page_title="Crypto Backtester",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

from ui.sidebar import render_sidebar
from ui.charts import render_price_chart, render_equity_chart, render_indicator_chart
from ui.metrics_table import render_metrics
from data.fetcher import DataFetcher
from backtester.engine import Backtester


st.title("📈 Cryptocurrency Backtesting Platform")
st.caption("Test trading strategies on historical Binance data")

config, strategy, symbol, timeframe, start_dt, end_dt = render_sidebar()

run = st.sidebar.button("▶ Run Backtest", type="primary", use_container_width=True)

if run:
    with st.spinner(f"Downloading {symbol} {timeframe} data..."):
        try:
            fetcher = DataFetcher()
            df = fetcher.fetch(symbol, timeframe, start_dt, end_dt)
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")
            st.stop()

    st.info(
        f"Loaded **{len(df):,}** candles for **{symbol}** "
        f"({timeframe}) from {df.index[0].date()} to {df.index[-1].date()}"
    )

    with st.spinner("Running backtest..."):
        result = Backtester(config).run(df, strategy)

    # --- Layout ---
    col_charts, col_metrics = st.columns([3, 1], gap="medium")

    with col_charts:
        st.plotly_chart(
            render_price_chart(df, result.signals_df, result.trades_df),
            use_container_width=True,
        )
        st.plotly_chart(
            render_equity_chart(result.equity_df, config.initial_capital),
            use_container_width=True,
        )

        # Optional indicator subplot
        with st.expander("Show RSI indicator"):
            from indicators.registry import IndicatorLibrary
            lib = IndicatorLibrary(df)
            rsi = lib.rsi()
            st.plotly_chart(
                render_indicator_chart(df, rsi, "RSI (14)", hlines=[30, 70]),
                use_container_width=True,
            )

    with col_metrics:
        render_metrics(result.metrics)

    # Trade log
    if not result.trades_df.empty:
        with st.expander(f"Trade Log ({len(result.trades_df)} trades)"):
            display_df = result.trades_df.copy()
            display_df["pnl"] = display_df["pnl"].round(2)
            display_df["pnl_pct"] = (display_df["pnl_pct"] * 100).round(2)
            display_df.columns = [c.replace("_", " ").title() for c in display_df.columns]
            st.dataframe(display_df, use_container_width=True)
    else:
        st.warning("No completed trades in this period.")

else:
    st.info("Configure your strategy in the sidebar and click **▶ Run Backtest**.")
