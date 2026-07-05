import datetime

from sqlalchemy import select

from app.models import FinancialFact, FinancialPeriod
from app.models.enums import PeriodType
from scripts.ingest import H1_SHARE_OF_YEAR, _model_monthly
from tests.factories import add_period


async def test_monthly_split_uses_reported_half_year_when_available(session_factory):
    async with session_factory() as session:
        await add_period(
            session,
            label="FY2025",
            period_type=PeriodType.ANNUAL,
            fiscal_year=2025,
            start_date=datetime.date(2024, 7, 1),
            end_date=datetime.date(2025, 6, 30),
            facts={"revenue": 1000.0},
        )
        await add_period(
            session,
            label="HY2025",
            period_type=PeriodType.HALF_YEAR,
            fiscal_year=2025,
            start_date=datetime.date(2024, 7, 1),
            end_date=datetime.date(2024, 12, 31),
            facts={"revenue": 300.0},  # a REPORTED H1 actual, not the seasonality assumption
        )

    await _model_monthly(session_factory)

    async with session_factory() as session:
        jul = await session.scalar(select(FinancialPeriod).where(FinancialPeriod.label == "Jul 2024"))
        jan = await session.scalar(select(FinancialPeriod).where(FinancialPeriod.label == "Jan 2025"))
        jul_revenue = await session.scalar(
            select(FinancialFact.value).where(
                FinancialFact.period_id == jul.id, FinancialFact.metric_key == "revenue"
            )
        )
        jan_revenue = await session.scalar(
            select(FinancialFact.value).where(
                FinancialFact.period_id == jan.id, FinancialFact.metric_key == "revenue"
            )
        )
        assert float(jul_revenue) == 50.0  # 300 (REPORTED H1) / 6
        assert float(jan_revenue) == round(700.0 / 6, 2)  # (1000 total - 300 REPORTED H1) / 6


async def test_monthly_split_falls_back_to_assumption_without_reported_half_year(session_factory):
    async with session_factory() as session:
        await add_period(
            session,
            label="FY2024",
            period_type=PeriodType.ANNUAL,
            fiscal_year=2024,
            start_date=datetime.date(2023, 7, 1),
            end_date=datetime.date(2024, 6, 30),
            facts={"revenue": 1000.0},
        )

    await _model_monthly(session_factory)

    async with session_factory() as session:
        jul = await session.scalar(select(FinancialPeriod).where(FinancialPeriod.label == "Jul 2023"))
        jul_revenue = await session.scalar(
            select(FinancialFact.value).where(
                FinancialFact.period_id == jul.id, FinancialFact.metric_key == "revenue"
            )
        )
        # no other fiscal year in this empty test schema has a REPORTED half-year to measure a
        # ratio from, so it falls back to the documented default assumption
        assert float(jul_revenue) == round(1000.0 * H1_SHARE_OF_YEAR / 6, 2)
