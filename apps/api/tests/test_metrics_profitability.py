from app.services.metrics import compute_profitability
from tests.factories import add_annual_period, add_user, login


async def test_compute_profitability_calculates_margins_and_ebitda(session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={
                "revenue": 836991.0,
                "gross_profit": 648450.0,
                "operating_profit": -633694.0,
                "depreciation": 20381.0,
            },
        )

    async with session_factory() as session:
        results = await compute_profitability(session)

    assert len(results) == 1
    period = results[0]
    assert period.period_label == "FY2025"

    # gross_margin = 648450 / 836991
    assert period.metrics["gross_margin"].value == round(648450.0 / 836991.0 * 100, 2)
    assert period.metrics["gross_margin"].unit == "%"

    # ebitda = operating_profit + depreciation = -633694 + 20381
    assert period.metrics["ebitda"].value == round(-633694.0 + 20381.0, 2)
    assert period.metrics["ebitda"].unit == "EUR"
    # a loss-making period should show a negative EBITDA, not an error
    assert period.metrics["ebitda"].value < 0


async def test_compute_profitability_omits_ebitda_without_depreciation_fact(session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={"revenue": 1000.0, "gross_profit": 500.0, "operating_profit": -100.0},
        )

    async with session_factory() as session:
        results = await compute_profitability(session)

    assert "ebitda" not in results[0].metrics
    assert "ebitda_margin" not in results[0].metrics
    assert "gross_margin" in results[0].metrics  # unaffected, doesn't need depreciation


async def test_compute_profitability_includes_cost_breakdown_when_disclosed(session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={
                "revenue": 836991.0,
                "gross_profit": 648450.0,
                "operating_profit": -633694.0,
                "cost_of_sales": 188541.0,
                "admin_expenses": 1286058.0,
                # no distribution_costs fact for this period: not disclosed
            },
        )

    async with session_factory() as session:
        results = await compute_profitability(session)

    metrics = results[0].metrics
    assert metrics["cost_of_sales"].value == 188541.0
    assert metrics["cost_of_sales"].unit == "EUR"
    assert metrics["admin_expenses"].value == 1286058.0
    assert "distribution_costs" not in metrics


async def test_profitability_endpoint_requires_auth(client):
    response = await client.get("/metrics/profitability")
    assert response.status_code == 401


async def test_profitability_endpoint_returns_computed_metrics(client, session_factory):
    async with session_factory() as session:
        await add_annual_period(
            session,
            label="FY2025",
            fiscal_year=2025,
            facts={
                "revenue": 836991.0,
                "gross_profit": 648450.0,
                "operating_profit": -633694.0,
                "depreciation": 20381.0,
            },
        )
        await add_user(session)

    token = await login(client)
    response = await client.get(
        "/metrics/profitability", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["period_label"] == "FY2025"
    assert "description" in body[0]["metrics"]["ebitda"]
