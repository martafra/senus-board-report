from app.services.metrics import compute_returns
from tests.factories import add_annual_period, add_user, login


async def test_roce_computed_from_balance_sheet_components(session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={
                "operating_profit": -100.0,
                "tangible_assets": 200.0,
                "debtors": 300.0,
                "cash_end": 400.0,
                "creditors_current": -150.0,
            },
        )

    async with session_factory() as session:
        results = await compute_returns(session)

    # total_assets = 200 + 300 + 400 = 900; capital_employed = 900 - 150 = 750
    assert results[0].metrics["roce"].value == round(-100.0 / 750.0 * 100, 2)
    assert results[0].metrics["roce"].unit == "%"


async def test_roce_includes_goodwill_and_development_costs_when_present(session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="HY2026",
            fiscal_year=2026,
            facts={
                "operating_profit": -483753.0,
                "tangible_assets": 42006.0,
                "debtors": 188149.0,
                "cash_end": 735189.0,
                "creditors_current": -387105.0,
                "goodwill": 669550.0,
                "development_costs": 239765.0,
            },
        )

    async with session_factory() as session:
        results = await compute_returns(session)

    total_assets = 42006.0 + 188149.0 + 735189.0 + 669550.0 + 239765.0
    capital_employed = total_assets - 387105.0
    assert results[0].metrics["roce"].value == round(-483753.0 / capital_employed * 100, 2)


async def test_roce_omitted_when_a_required_fact_is_missing(session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={"operating_profit": -100.0, "tangible_assets": 200.0},  # missing debtors etc.
        )

    async with session_factory() as session:
        results = await compute_returns(session)

    assert "roce" not in results[0].metrics


async def test_returns_endpoint_requires_auth(client):
    response = await client.get("/metrics/returns")
    assert response.status_code == 401


async def test_returns_endpoint_returns_computed_metrics(client, session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={
                "operating_profit": -100.0,
                "tangible_assets": 200.0,
                "debtors": 300.0,
                "cash_end": 400.0,
                "creditors_current": -150.0,
            },
        )
        await add_user(session)

    token = await login(client)
    response = await client.get("/metrics/returns", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert "roce" in response.json()[0]["metrics"]
