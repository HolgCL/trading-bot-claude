# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the Streamlit web UI
.venv/bin/streamlit run app/main.py

# Install dependencies
.venv/bin/pip install -r requirements.txt

# Run tests
.venv/bin/pytest tests/ -v

# Run a single test file
.venv/bin/pytest tests/test_backtester.py -v

# Quick smoke test (no Binance connection needed)
.venv/bin/python -c "from backtester.engine import Backtester; print('OK')"
```

## Architecture

The platform has five layers that flow left-to-right:

**Data → Indicators → Strategy → Backtester → UI**

### Data layer (`data/`)
`DataFetcher` fetches OHLCV candles from Binance via `ccxt`, paginates automatically, and delegates caching to `CacheManager` (parquet files in `cache/`). Cache key is `{symbol}_{timeframe}_{start}_{end}.parquet`. Returns a `pd.DataFrame` with a UTC `DatetimeTzDtype` index and float columns `open/high/low/close/volume`.

### Indicators layer (`indicators/`)
`IndicatorLibrary` is injected into every strategy as `self.indicators`. It wraps the `ta` library behind named methods and caches results within a single backtest run:

| Method | Returns | Notes |
|---|---|---|
| `rsi(period=14)` | `Series` | |
| `macd(fast, slow, signal)` | `DataFrame[macd, signal, histogram]` | |
| `bbands(period, std_dev)` | `DataFrame[lower, mid, upper]` | |
| `sma(period)` / `ema(period)` | `Series` | |
| `obv()` | `Series` | |
| `vwap(period)` | `Series` | Rolling VWAP |
| `keltner(period=20, multiplier=2.25)` | `DataFrame[lower, mid, upper]` | EMA ± ATR×multiplier |

Custom and ML-based indicators are registered via `library.register(indicator)` and called via `self.indicators.custom("name")`. `MLIndicator` wraps any sklearn-compatible model and applies a 1-bar shift to prevent look-ahead.

### Strategy layer (`strategies/`)
All strategies subclass `Strategy` (in `strategies/base.py`) and implement `generate_signals(df) -> pd.Series` returning `Signal.BUY / SELL / HOLD` for every bar. The indicator library is injected by the backtester before `generate_signals` is called — strategies must not instantiate `IndicatorLibrary` themselves. Strategy parameters are set in `__init__`; `get_params()` is used by the UI to display them.

### Backtester (`backtester/`)
`Backtester.run(df, strategy)` orchestrates the full pipeline:
1. Injects `IndicatorLibrary` into the strategy
2. Calls `generate_signals()` — vectorised over all bars at once
3. Simulates execution: signal on bar `i` → execute on `open[i+1]` (no look-ahead)
4. `Portfolio` tracks cash, open position (long-only), commission (% of trade value), trades, and equity curve
5. `MetricsCalculator` computes all metrics from the equity curve and trade list

Returns a `BacktestResult` dataclass with `equity_df`, `trades_df`, `signals_df`, `metrics`, `orders`, `config`.

`BacktestConfig` holds `initial_capital`, `commission_rate`, `signal_fraction` (fraction of cash per BUY), and `timeframe` (used to annualise Sharpe/Sortino correctly).

### UI (`ui/` + `app/main.py`)
Streamlit app. `ui/sidebar.py` renders all controls and returns `(config, strategy, symbol, timeframe, start_dt, end_dt)`. Charts are Plotly figures returned by functions in `ui/charts.py` and rendered with `st.plotly_chart`. The UI re-runs a full backtest on every sidebar interaction (Streamlit's default rerun model).

When `KeltnerMACDStrategy` is selected, `app/main.py` renders dedicated `render_keltner_chart()` and `render_macd_chart()` expanders instead of the default RSI panel.

## Available strategies

| File | Class | Description |
|---|---|---|
| `strategies/rsi_mean_reversion.py` | `RSIMeanReversionStrategy` | Buy oversold RSI, sell overbought; optional SMA trend filter |
| `strategies/macd_crossover.py` | `MACDCrossoverStrategy` | Buy on bullish MACD crossover, sell on bearish |
| `strategies/keltner_macd.py` | `KeltnerMACDStrategy` | Buy at KC lower band + MACD histogram reversal; exit at mid or upper band |

## Adding a new strategy

1. Create `strategies/my_strategy.py` subclassing `Strategy`
2. Add it to `STRATEGY_MAP` in `ui/sidebar.py`
3. Add parameter sliders in `_build_strategy()` in `ui/sidebar.py`

## Key design constraints

- **Signal execution**: signals are always vectorised (whole DataFrame at once), never bar-by-bar in Python. This keeps backtests fast but means `generate_signals` must avoid using future data.
- **Long-only**: `Portfolio` only tracks a single long position. Short selling is not implemented.
- **Timeframe annualisation**: pass the correct `timeframe` in `BacktestConfig` so Sharpe/Sortino are annualised with the right factor (see `_CANDLES_PER_YEAR` in `backtester/engine.py`).
- **No Binance API key required**: public endpoints are used for historical data. `DataFetcher` accepts optional `api_key`/`api_secret` for private endpoints.
