from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from strategies.base import Signal


def render_price_chart(
    df: pd.DataFrame,
    signals_df: pd.DataFrame,
    trades_df: pd.DataFrame,
) -> go.Figure:
    """
    Candlestick chart with BUY/SELL markers and trade annotations.
    Returns a Plotly Figure (caller calls st.plotly_chart on it).
    """
    fig = make_subplots(rows=1, cols=1)

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        name="Price",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
    ))

    # BUY markers (green triangles)
    buys = signals_df[signals_df["signal"] == Signal.BUY]
    if not buys.empty:
        fig.add_trace(go.Scatter(
            x=buys.index,
            y=buys["close"] * 0.995,
            mode="markers",
            marker=dict(symbol="triangle-up", size=10, color="#26a69a"),
            name="BUY",
        ))

    # SELL markers (red triangles)
    sells = signals_df[signals_df["signal"] == Signal.SELL]
    if not sells.empty:
        fig.add_trace(go.Scatter(
            x=sells.index,
            y=sells["close"] * 1.005,
            mode="markers",
            marker=dict(symbol="triangle-down", size=10, color="#ef5350"),
            name="SELL",
        ))

    fig.update_layout(
        title="Price Chart with Signals",
        xaxis_rangeslider_visible=False,
        height=500,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def render_equity_chart(equity_df: pd.DataFrame, initial_capital: float) -> go.Figure:
    """Equity curve with buy-and-hold benchmark."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=equity_df.index,
        y=equity_df["equity"],
        mode="lines",
        name="Strategy Equity",
        line=dict(color="#42a5f5", width=2),
    ))

    # Flat line at initial capital for reference
    fig.add_hline(
        y=initial_capital,
        line_dash="dash",
        line_color="gray",
        annotation_text="Initial Capital",
    )

    fig.update_layout(
        title="Equity Curve",
        yaxis_title="Portfolio Value (USDT)",
        height=350,
        template="plotly_dark",
    )
    return fig


def render_indicator_chart(
    df: pd.DataFrame,
    indicator_series: pd.Series,
    title: str,
    hlines: list[float] | None = None,
) -> go.Figure:
    """Generic indicator subplot (e.g. RSI, MACD histogram)."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=indicator_series.index,
        y=indicator_series.values,
        mode="lines",
        name=title,
        line=dict(color="#ab47bc", width=1.5),
    ))
    for level in (hlines or []):
        fig.add_hline(y=level, line_dash="dot", line_color="gray")
    fig.update_layout(title=title, height=220, template="plotly_dark")
    return fig


def render_keltner_chart(df: pd.DataFrame, kc: pd.DataFrame) -> go.Figure:
    """Price chart with Keltner Channel bands overlaid."""
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        name="Price",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
    ))
    fig.add_trace(go.Scatter(
        x=kc.index, y=kc["upper"],
        mode="lines", name="KC Upper",
        line=dict(color="#ff9800", width=1, dash="dot"),
    ))
    fig.add_trace(go.Scatter(
        x=kc.index, y=kc["mid"],
        mode="lines", name="KC Mid (EMA)",
        line=dict(color="#ffeb3b", width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=kc.index, y=kc["lower"],
        mode="lines", name="KC Lower",
        line=dict(color="#ff9800", width=1, dash="dot"),
        fill="tonexty",
        fillcolor="rgba(255, 152, 0, 0.05)",
    ))
    fig.update_layout(
        title="Keltner Channel (period=20, ATR×2.25)",
        xaxis_rangeslider_visible=False,
        height=450,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def render_macd_chart(macd_df: pd.DataFrame) -> go.Figure:
    """MACD line, signal line, and histogram."""
    fig = make_subplots(rows=1, cols=1)

    colors = ["#26a69a" if v >= 0 else "#ef5350" for v in macd_df["histogram"]]
    fig.add_trace(go.Bar(
        x=macd_df.index, y=macd_df["histogram"],
        name="Histogram", marker_color=colors, opacity=0.7,
    ))
    fig.add_trace(go.Scatter(
        x=macd_df.index, y=macd_df["macd"],
        mode="lines", name="MACD",
        line=dict(color="#42a5f5", width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=macd_df.index, y=macd_df["signal"],
        mode="lines", name="Signal",
        line=dict(color="#ff7043", width=1.5),
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    fig.update_layout(
        title="MACD (12, 26, 9)",
        height=250,
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig
