"""
Pydantic v2 models for the /api/v1/backtest endpoint (Premium).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request body
# ---------------------------------------------------------------------------

class BacktestRequest(BaseModel):
    symbol: str = Field(
        ...,
        description="Stock ticker symbol.",
        examples=["2330.TW"],
    )
    initial_capital: float = Field(
        100_000.0,
        gt=0,
        description="Starting capital in local currency.",
        examples=[100_000.0],
    )
    ma_short: int = Field(
        20,
        ge=5,
        le=100,
        description="Short moving-average window (days).",
        examples=[20],
    )
    ma_long: int = Field(
        60,
        ge=10,
        le=300,
        description="Long moving-average window (days).",
        examples=[60],
    )
    take_profit_pct: float = Field(
        0.15,
        gt=0,
        lt=1,
        description="Take-profit threshold as a decimal fraction (e.g. 0.15 = 15%).",
        examples=[0.15],
    )
    stop_loss_pct: float = Field(
        0.08,
        gt=0,
        lt=1,
        description="Stop-loss threshold as a decimal fraction (e.g. 0.08 = 8%).",
        examples=[0.08],
    )
    lookback_days: int = Field(
        365,
        ge=90,
        le=1825,
        description="Number of historical calendar days to include in the simulation.",
        examples=[365],
    )


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class EquityCurvePoint(BaseModel):
    date: str = Field(..., description="ISO-8601 date string.", examples=["2024-01-15"])
    equity: float = Field(..., description="Portfolio equity value on that date.", examples=[108_320.5])


class BacktestMetrics(BaseModel):
    total_return_pct: float = Field(..., description="Total return as a percentage.", examples=[8.32])
    max_drawdown_pct: float = Field(..., description="Maximum drawdown as a percentage.", examples=[-12.5])
    sharpe_ratio: float | None = Field(None, description="Annualised Sharpe ratio.", examples=[1.12])
    num_trades: int = Field(..., description="Total number of trades executed.", examples=[14])
    win_rate_pct: float = Field(..., description="Percentage of winning trades.", examples=[57.14])


class BacktestResponse(BaseModel):
    symbol: str
    strategy: str = Field(..., description="Human-readable strategy description.", examples=["MA-Crossover (20/60)"])
    metrics: BacktestMetrics
    equity_curve: list[EquityCurvePoint] = Field(
        ...,
        description="Time-series of portfolio equity for chart rendering.",
    )
