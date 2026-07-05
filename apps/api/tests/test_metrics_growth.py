import datetime

from app.models.enums import CustomerChannel, PeriodType
from app.services.metrics import compute_growth
from tests.factories import add_annual_period, add_customer_metric, add_period, add_user, login


async def test_yoy_growth_compares_same_period_type_one_year_earlier(session_factory):
    async with session_factory() as session:
        await add_annual_period(session, label="FY2024", fiscal_year=2024, facts={"revenue": 688317.0})
        await add_annual_period(session, label="FY2025", fiscal_year=2025, facts={"revenue": 836991.0})

    async with session_factory() as session:
        results = await compute_growth(session)

    fy2025 = next(r for r in results if r.period_label == "FY2025")
    assert fy2025.metrics["yoy_growth"].value == round((836991.0 - 688317.0) / 688317.0 * 100, 2)

    fy2024 = next(r for r in results if r.period_label == "FY2024")
    assert "yoy_growth" not in fy2024.metrics  # no FY2023 to compare against


async def test_yoy_growth_does_not_mix_period_types(session_factory):
    async with session_factory() as session:
        # a HALF_YEAR starting the same date as an ANNUAL period must not be treated as its YoY
        # comparator: they are different kinds of period even though the start_date matches.
        await add_annual_period(session, label="FY2025", fiscal_year=2025, facts={"revenue": 1000.0})
        await add_period(
            session,
            label="HY2025",
            period_type=PeriodType.HALF_YEAR,
            fiscal_year=2025,
            start_date=datetime.date(2024, 7, 1),
            end_date=datetime.date(2024, 12, 31),
            facts={"revenue": 400.0},
        )

    async with session_factory() as session:
        results = await compute_growth(session)

    fy2025 = next(r for r in results if r.period_label == "FY2025")
    assert "yoy_growth" not in fy2025.metrics


async def test_mom_growth_only_applies_to_monthly_periods(session_factory):
    async with session_factory() as session:
        await add_period(
            session,
            label="Jun 2024",
            period_type=PeriodType.MONTHLY,
            fiscal_year=2024,
            start_date=datetime.date(2024, 6, 1),
            end_date=datetime.date(2024, 7, 1),
            is_actual_reported=False,
            facts={"revenue": 100.0},
        )
        await add_period(
            session,
            label="Jul 2024",
            period_type=PeriodType.MONTHLY,
            fiscal_year=2025,
            start_date=datetime.date(2024, 7, 1),
            end_date=datetime.date(2024, 8, 1),
            is_actual_reported=False,
            facts={"revenue": 120.0},
        )

    async with session_factory() as session:
        results = await compute_growth(session)

    jul = next(r for r in results if r.period_label == "Jul 2024")
    assert jul.metrics["mom_growth"].value == round((120.0 - 100.0) / 100.0 * 100, 2)

    jun = next(r for r in results if r.period_label == "Jun 2024")
    assert "mom_growth" not in jun.metrics  # no prior month in this test's data


async def test_customer_counts_and_bookings_are_included_when_present(session_factory):
    async with session_factory() as session:
        period = await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={"revenue": 836991.0, "new_bookings_value_period": 700000.0},
        )
        await add_customer_metric(
            session, period=period, channel=CustomerChannel.ENTERPRISE, customer_count=36
        )

    async with session_factory() as session:
        results = await compute_growth(session)

    fy2025 = results[0]
    assert fy2025.metrics["customers_enterprise"].value == 36
    assert fy2025.metrics["customers_enterprise"].unit == "count"
    assert fy2025.metrics["new_bookings_value_period"].value == 700000.0


async def test_growth_endpoint_requires_auth(client):
    response = await client.get("/metrics/growth")
    assert response.status_code == 401


async def test_growth_endpoint_returns_computed_metrics(client, session_factory):
    async with session_factory() as session:
        await add_annual_period(session, label="FY2025", fiscal_year=2025, facts={"revenue": 836991.0})
        await add_user(session)

    token = await login(client)
    response = await client.get("/metrics/growth", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()[0]["metrics"]["revenue"]["value"] == 836991.0
