import datetime

from app.models.enums import PeriodType
from app.services.metrics import compute_solvency
from tests.factories import add_annual_period, add_period, add_user, login


async def test_dscr_computed_when_all_inputs_present(session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={
                "operating_profit": -633694.0,
                "depreciation": 20381.0,
                "interest_expense": 2074.0,
                "loans_repayable_one_year_or_less": 10112.0,
            },
        )

    async with session_factory() as session:
        results = await compute_solvency(session)

    ebitda = -633694.0 + 20381.0
    debt_service = 2074.0 + 10112.0
    assert results[0].metrics["dscr"].value == round(ebitda / debt_service, 2)
    assert results[0].metrics["dscr"].unit == "x"


async def test_dscr_omitted_without_loan_repayment_schedule(session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={
                "operating_profit": -633694.0,
                "depreciation": 20381.0,
                "interest_expense": 2074.0,
                # no loans_repayable_one_year_or_less: not disclosed at this granularity
            },
        )

    async with session_factory() as session:
        results = await compute_solvency(session)

    assert "dscr" not in results[0].metrics


async def test_solvency_only_includes_annual_periods(session_factory):
    async with session_factory() as session:
        await add_annual_period(session, label="FY2025", fiscal_year=2025, facts={"revenue": 1000.0})
        await add_period(
            session,
            label="HY2026",
            period_type=PeriodType.HALF_YEAR,
            fiscal_year=2026,
            start_date=datetime.date(2025, 7, 1),
            end_date=datetime.date(2025, 12, 31),
            facts={
                "operating_profit": -1000.0,
                "depreciation": 100.0,
                "interest_expense": 50.0,
                "loans_repayable_one_year_or_less": 10.0,
            },
        )

    async with session_factory() as session:
        results = await compute_solvency(session)

    assert len(results) == 1
    assert results[0].period_label == "FY2025"


async def test_solvency_endpoint_requires_auth(client):
    response = await client.get("/metrics/solvency")
    assert response.status_code == 401


async def test_solvency_endpoint_returns_computed_metrics(client, session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={
                "operating_profit": -633694.0,
                "depreciation": 20381.0,
                "interest_expense": 2074.0,
                "loans_repayable_one_year_or_less": 10112.0,
            },
        )
        await add_user(session)

    token = await login(client)
    response = await client.get("/metrics/solvency", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert "dscr" in response.json()[0]["metrics"]
