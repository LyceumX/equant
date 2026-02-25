"""
qlib_wrapper.py — Technical indicator calculator.

MOCK-FIRST PRINCIPLE
--------------------
All calculations use pure Pandas/NumPy so the API chain works Day 1 without
installing Qlib's heavy C extensions.  When you are ready to upgrade, replace
the `_calc_*` functions below with real qlib expressions; the public interface
stays identical.
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def compute_indicators(ohlcv: list[dict]) -> dict:
    """
    Given a list of OHLCV dicts (keys: date, open, high, low, close, volume),
    return a dict of computed technical indicators.

    Returns:
        {
            "rsi": float,
            "macd": "bullish" | "bearish" | "neutral",
            "ma20": float | None,
            "ma60": float | None,
        }
    """
    try:
        df = _to_dataframe(ohlcv)
        rsi = _calc_rsi(df["close"], period=14)
        macd_signal = _calc_macd_signal(df["close"])
        ma20 = _calc_ma(df["close"], 20)
        ma60 = _calc_ma(df["close"], 60)

        return {
            "rsi": round(float(rsi), 2),
            "macd": macd_signal,
            "ma20": round(float(ma20), 2) if ma20 is not None else None,
            "ma60": round(float(ma60), 2) if ma60 is not None else None,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("compute_indicators failed: %s — returning defaults", exc)
        return {"rsi": 50.0, "macd": "neutral", "ma20": None, "ma60": None}


# ---------------------------------------------------------------------------
# Internal helpers (pure Pandas — swap with Qlib expressions in Phase 2)
# ---------------------------------------------------------------------------


def _to_dataframe(ohlcv: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(ohlcv)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["close"]).reset_index(drop=True)
    return df


def _calc_rsi(series: pd.Series, period: int = 14) -> float:
    """Wilder-smoothed RSI."""
    if len(series) < period + 1:
        return 50.0  # not enough data

    delta = series.diff().dropna()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, float("nan"))
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not rsi.empty else 50.0


def _calc_macd_signal(series: pd.Series) -> str:
    """
    Returns 'bullish' if MACD line > Signal line, 'bearish' otherwise.
    Falls back to 'neutral' on insufficient data.
    """
    if len(series) < 26:
        return "neutral"

    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()

    if macd_line.iloc[-1] > signal_line.iloc[-1]:
        return "bullish"
    elif macd_line.iloc[-1] < signal_line.iloc[-1]:
        return "bearish"
    return "neutral"


def _calc_ma(series: pd.Series, window: int) -> float | None:
    if len(series) < window:
        return None
    return float(series.rolling(window=window).mean().iloc[-1])
