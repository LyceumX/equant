"""
backtest.py — POST /api/v1/backtest  (Premium users only)

Business logic:
  1. Validate Premium access via get_premium_user dependency
  2. Delegate to finrl_mock.run_backtest
  3. Return typed BacktestResponse
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_premium_user
from app.schemas.backtest import BacktestRequest, BacktestResponse
from app.services import finrl_mock

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/backtest",
    response_model=BacktestResponse,
    summary="Strategy backtesting simulation (Premium)",
    description=(
        "Accepts simple MA-crossover strategy parameters and returns an equity "
        "curve + performance metrics.  Requires a Premium Clerk JWT."
    ),
)
async def run_backtest(
    body: BacktestRequest,
    _user: Annotated[dict[str, Any], Depends(get_premium_user)],
) -> BacktestResponse:
    if body.ma_short >= body.ma_long:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ma_short must be strictly less than ma_long.",
        )

    try:
        result = await finrl_mock.run_backtest(
            symbol=body.symbol,
            initial_capital=body.initial_capital,
            ma_short=body.ma_short,
            ma_long=body.ma_long,
            take_profit_pct=body.take_profit_pct,
            stop_loss_pct=body.stop_loss_pct,
            lookback_days=body.lookback_days,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("run_backtest(%s): %s", body.symbol, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backtest simulation failed.",
        ) from exc

    return BacktestResponse(
        symbol=body.symbol,
        strategy=result["strategy"],
        metrics=result["metrics"],
        equity_curve=result["equity_curve"],
    )
