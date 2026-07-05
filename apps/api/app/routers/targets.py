from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models import DebtInstrument, KPITarget, User
from app.schemas.targets import DebtInstrumentOut, KPITargetOut

router = APIRouter(prefix="/targets", tags=["targets"])


@router.get("/kpi", response_model=list[KPITargetOut])
async def get_kpi_targets(
    session: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[KPITargetOut]:
    targets = (
        await session.scalars(select(KPITarget).order_by(KPITarget.target_date))
    ).all()
    return [
        KPITargetOut(
            name=t.name,
            target_value=float(t.target_value),
            target_date=t.target_date.isoformat(),
            description=t.description,
        )
        for t in targets
    ]


@router.get("/debt", response_model=list[DebtInstrumentOut])
async def get_debt_instruments(
    session: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[DebtInstrumentOut]:
    instruments = (
        await session.scalars(select(DebtInstrument).order_by(DebtInstrument.start_date))
    ).all()
    return [
        DebtInstrumentOut(
            name=d.name,
            principal=float(d.principal),
            start_date=d.start_date.isoformat(),
            provider=d.provider,
            repaid_date=d.repaid_date.isoformat() if d.repaid_date else None,
            note=d.note,
        )
        for d in instruments
    ]
