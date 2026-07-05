from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.metrics import PeriodMetrics
from app.services import metrics as metrics_service

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/growth", response_model=list[PeriodMetrics])
async def get_growth(
    session: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[PeriodMetrics]:
    return await metrics_service.compute_growth(session)


@router.get("/profitability", response_model=list[PeriodMetrics])
async def get_profitability(
    session: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[PeriodMetrics]:
    return await metrics_service.compute_profitability(session)


@router.get("/cash-liquidity", response_model=list[PeriodMetrics])
async def get_cash_liquidity(
    session: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[PeriodMetrics]:
    return await metrics_service.compute_cash_liquidity(session)


@router.get("/solvency", response_model=list[PeriodMetrics])
async def get_solvency(
    session: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[PeriodMetrics]:
    return await metrics_service.compute_solvency(session)


@router.get("/returns", response_model=list[PeriodMetrics])
async def get_returns(
    session: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[PeriodMetrics]:
    return await metrics_service.compute_returns(session)
