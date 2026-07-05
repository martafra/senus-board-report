from fastapi import APIRouter, Depends, HTTPException
from google.genai.errors import APIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.insights import InsightOut
from app.services import insights as insights_service
from app.services import metrics as metrics_service

router = APIRouter(prefix="/insights", tags=["insights"])

SECTION_COMPUTE = {
    "growth": metrics_service.compute_growth,
    "profitability": metrics_service.compute_profitability,
    "cash-liquidity": metrics_service.compute_cash_liquidity,
    "solvency": metrics_service.compute_solvency,
    "returns": metrics_service.compute_returns,
}


async def _compute_section_metrics(section: str, session: AsyncSession):
    compute_fn = SECTION_COMPUTE.get(section)
    if compute_fn is None:
        raise HTTPException(status_code=404, detail=f"Unknown section '{section}'")
    return await compute_fn(session)


async def _get_or_generate(
    section: str, session: AsyncSession, *, force_regenerate: bool
) -> InsightOut:
    metrics = await _compute_section_metrics(section, session)
    try:
        insight = await insights_service.get_or_generate_insight(
            session, section, metrics, force_regenerate=force_regenerate
        )
    except APIError as exc:
        # Most commonly the Gemini free tier's daily/per-minute request quota (a real, expected
        # constraint of this project's free-tier choice, not a bug): surface a clear, actionable
        # message instead of a bare 500 with an internal traceback.
        raise HTTPException(
            status_code=503,
            detail=(
                "AI insight generation is temporarily unavailable (the underlying AI service "
                f"returned an error: {exc.message}). Please try again shortly."
            ),
        ) from exc
    return InsightOut.model_validate(insight)


@router.get("/{section}", response_model=InsightOut)
async def get_insight(
    section: str,
    session: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> InsightOut:
    return await _get_or_generate(section, session, force_regenerate=False)


@router.post("/{section}/regenerate", response_model=InsightOut)
async def regenerate_insight(
    section: str,
    session: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> InsightOut:
    return await _get_or_generate(section, session, force_regenerate=True)
