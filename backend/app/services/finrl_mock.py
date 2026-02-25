"""
finrl_mock.py — MA-crossover strategy backtester.

MOCK-FIRST PRINCIPLE
--------------------
Implements a moving-average-crossover backtest loop using pure Pandas.
The public interface mirrors what a real FinRL environment would expose so
swapping in the real FinRL `StockTradingEnv` later requires only changes
inside `run_backtest()`, not in the API layer.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

import pandas as pd

from app.services.data_fetcher import fetch_market_data

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


async def run_backtest(
    symbol: str,
    initial_capital: float,
    ma_short: int,
    ma_long: int,
    take_profit_pct: float,
    stop_loss_pct: float,
    lookback_days: int,
) -> dict:
    """
    Run a simple MA-crossover strategy simulation.

    Returns:
        {
            "strategy": str,
            "metrics": {total_return_pct, max_drawdown_pct, sharpe_ratio,
                        num_trades, win_rate_pct},
            "equity_curve": [{"date": str, "equity": float}, ...]
        }
    """
    market = await fetch_market_data(symbol, days=lookback_days)
    ohlcv = market["ohlcv"]

    if len(ohlcv) < ma_long + 5:
        raise ValueError(
            f"Not enough data: need at least {ma_long + 5} days, got {len(ohlcv)}."
        )

    df = pd.DataFrame(ohlcv)[["date", "close"]].copy()
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["close"]).reset_index(drop=True)

    df[f"ma{ma_short}"] = df["close"].rolling(ma_short).mean()
    df[f"ma{ma_long}"] = df["close"].rolling(ma_long).mean()
    df = df.dropna().reset_index(drop=True)

    # ── Simulate strategy ─────────────────────────────────────────────────
    equity = initial_capital
    position = 0.0        # number of shares held
    entry_price = 0.0
    trade_results: list[float] = []
    equity_curve: list[dict] = []

    prev_short = df[f"ma{ma_short}"].iloc[0]
    prev_long  = df[f"ma{ma_long}"].iloc[0]

    for i, row in df.iterrows():
        cur_short: float = row[f"ma{ma_short}"]
        cur_long: float  = row[f"ma{ma_long}"]
        price: float     = row["close"]

        # Golden cross → BUY
        if prev_short <= prev_long and cur_short > cur_long and position == 0:
            position = equity / price
            entry_price = price

        # Death cross OR take-profit / stop-loss → SELL
        elif position > 0:
            change = (price - entry_price) / entry_price
            should_sell = (
                (prev_short >= prev_long and cur_short < cur_long)
                or change >= take_profit_pct
                or change <= -stop_loss_pct
            )
            if should_sell:
                equity = position * price
                trade_results.append(price - entry_price)
                position = 0.0
                entry_price = 0.0

        current_equity = (position * price + equity) if position > 0 else equity
        equity_curve.append({"date": str(row["date"]), "equity": round(current_equity, 2)})

        prev_short = cur_short
        prev_long  = cur_long

    # Close open position at last price
    if position > 0:
        last_price = df["close"].iloc[-1]
        equity = position * last_price
        trade_results.append(last_price - entry_price)

    # ── Calculate metrics ─────────────────────────────────────────────────
    final_equity = equity_curve[-1]["equity"] if equity_curve else initial_capital
    total_return = (final_equity - initial_capital) / initial_capital * 100

    equities = pd.Series([p["equity"] for p in equity_curve])
    rolling_max = equities.cummax()
    drawdown = (equities - rolling_max) / rolling_max * 100
    max_drawdown = float(drawdown.min())

    daily_returns = equities.pct_change().dropna()
    mean_ret = daily_returns.mean()
    std_ret = daily_returns.std()
    sharpe = float((mean_ret / std_ret) * (252**0.5)) if std_ret and std_ret > 0 else None

    num_trades = len(trade_results)
    win_rate = (sum(1 for r in trade_results if r > 0) / num_trades * 100) if num_trades else 0.0

    return {
        "strategy": f"MA-Crossover ({ma_short}/{ma_long})",
        "metrics": {
            "total_return_pct": round(total_return, 2),
            "max_drawdown_pct": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe, 3) if sharpe is not None else None,
            "num_trades": num_trades,
            "win_rate_pct": round(win_rate, 2),
        },
        "equity_curve": equity_curve,
    }
