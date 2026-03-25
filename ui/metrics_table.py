import streamlit as st


def render_metrics(metrics: dict) -> None:
    """Display metrics in a formatted grid."""
    st.subheader("Performance Metrics")

    profit_metrics = {
        "Final Equity": f"${metrics['Final Equity']:,.2f}",
        "Total P&L": f"${metrics['Total P&L']:,.2f}",
        "Total Return %": f"{metrics['Total Return %']:.2f}%",
    }
    risk_metrics = {
        "Sharpe Ratio": f"{metrics['Sharpe Ratio']:.3f}",
        "Sortino Ratio": f"{metrics['Sortino Ratio']:.3f}",
        "Max Drawdown %": f"{metrics['Max Drawdown %']:.2f}%",
        "Calmar Ratio": f"{metrics['Calmar Ratio']:.3f}",
    }
    trade_metrics = {
        "Total Trades": str(metrics["Total Trades"]),
        "Win Rate %": f"{metrics['Win Rate %']:.2f}%",
        "Avg Win %": f"{metrics['Avg Win %']:.2f}%",
        "Avg Loss %": f"{metrics['Avg Loss %']:.2f}%",
        "Profit Factor": f"{metrics['Profit Factor']:.3f}",
        "Avg Trade Duration": metrics["Avg Trade Duration"],
    }

    st.markdown("**Returns**")
    for label, value in profit_metrics.items():
        col1, col2 = st.columns([2, 1])
        col1.write(label)
        # Colour P&L green/red
        if "P&L" in label or "Return" in label:
            is_positive = metrics["Total P&L"] >= 0
            col2.markdown(
                f"<span style='color:{'#26a69a' if is_positive else '#ef5350'}'>{value}</span>",
                unsafe_allow_html=True,
            )
        else:
            col2.write(value)

    st.markdown("**Risk**")
    for label, value in risk_metrics.items():
        col1, col2 = st.columns([2, 1])
        col1.write(label)
        col2.write(value)

    st.markdown("**Trades**")
    for label, value in trade_metrics.items():
        col1, col2 = st.columns([2, 1])
        col1.write(label)
        col2.write(value)
