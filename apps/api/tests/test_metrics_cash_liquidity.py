from app.services.metrics import compute_cash_liquidity
from tests.factories import add_annual_period, add_user, login


async def test_free_cash_flow_is_operating_plus_investing_cash_flow(session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={"cash_operating": -374820.0, "cash_investing": -3451.0},
        )

    async with session_factory() as session:
        results = await compute_cash_liquidity(session)

    assert results[0].metrics["free_cash_flow"].value == round(-374820.0 - 3451.0, 2)


async def test_cash_runway_computed_when_burning_cash(session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={"cash_operating": -120000.0, "cash_investing": 0.0, "cash_end": 60000.0},
        )

    async with session_factory() as session:
        results = await compute_cash_liquidity(session)

    # monthly burn = 120000 / 12 = 10000; runway = 60000 / 10000 = 6 months
    assert results[0].metrics["cash_runway_months"].value == 6.0
    assert results[0].metrics["cash_runway_months"].unit == "x"


async def test_cash_runway_omitted_when_not_burning_cash(session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={"cash_operating": 50000.0, "cash_investing": 0.0, "cash_end": 60000.0},
        )

    async with session_factory() as session:
        results = await compute_cash_liquidity(session)

    assert "cash_runway_months" not in results[0].metrics


async def test_working_capital_combines_debtors_cash_and_current_creditors(session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={"debtors": 50000.0, "cash_end": 60000.0, "creditors_current": -30000.0},
        )

    async with session_factory() as session:
        results = await compute_cash_liquidity(session)

    assert results[0].metrics["working_capital"].value == 50000.0 + 60000.0 - 30000.0


async def test_ebitda_to_fcf_bridge_steps_sum_to_free_cash_flow(session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={
                "operating_profit": -633694.0,
                "depreciation": 20381.0,
                "cash_operating": -374820.0,
                "cash_investing": -3451.0,
            },
        )

    async with session_factory() as session:
        results = await compute_cash_liquidity(session)

    metrics = results[0].metrics
    ebitda = metrics["ebitda"].value
    adjustments = metrics["operating_cash_adjustments"].value
    investing = metrics["cash_investing"].value
    fcf = metrics["free_cash_flow"].value

    assert investing == -3451.0
    assert round(ebitda + adjustments + investing, 2) == fcf


async def test_cash_liquidity_endpoint_requires_auth(client):
    response = await client.get("/metrics/cash-liquidity")
    assert response.status_code == 401


async def test_cash_liquidity_endpoint_returns_computed_metrics(client, session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={"cash_operating": -374820.0, "cash_investing": -3451.0},
        )
        await add_user(session)

    token = await login(client)
    response = await client.get(
        "/metrics/cash-liquidity", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert "free_cash_flow" in response.json()[0]["metrics"]
