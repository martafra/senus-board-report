import datetime

from app.models import DebtInstrument, KPITarget
from app.models.enums import Provenance
from tests.factories import add_user, login


async def test_kpi_targets_endpoint_requires_auth(client):
    response = await client.get("/targets/kpi")
    assert response.status_code == 401


async def test_debt_instruments_endpoint_requires_auth(client):
    response = await client.get("/targets/debt")
    assert response.status_code == 401


async def test_kpi_targets_endpoint_returns_targets_ordered_by_date(client, session_factory):
    async with session_factory() as session:
        session.add(
            KPITarget(
                name="Revenue CAGR",
                target_value=50.0,
                target_date=datetime.date(2030, 6, 30),
                description="Target: at least 50% CAGR.",
            )
        )
        session.add(
            KPITarget(
                name="EBITDA Positive",
                target_value=0.0,
                target_date=datetime.date(2028, 6, 30),
                description="Target: achieve positive EBITDA.",
            )
        )
        await add_user(session)
        await session.commit()

    token = await login(client)
    response = await client.get("/targets/kpi", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert [t["name"] for t in body] == ["EBITDA Positive", "Revenue CAGR"]  # earlier target_date first
    assert body[0]["description"] == "Target: achieve positive EBITDA."


async def test_debt_instruments_endpoint_distinguishes_repaid_from_outstanding(client, session_factory):
    async with session_factory() as session:
        session.add(
            DebtInstrument(
                name="Working Capital Loan - Test Director",
                principal=100000.0,
                start_date=datetime.date(2025, 3, 1),
                provider="Test Director",
                repaid_date=datetime.date(2025, 10, 31),
                note="Exact day not disclosed.",
                provenance=Provenance.REPORTED,
            )
        )
        session.add(
            DebtInstrument(
                name="SBCI backed term loan",
                principal=100000.0,
                start_date=datetime.date(2024, 7, 1),
                provider="SBCI",
                provenance=Provenance.REPORTED,
            )
        )
        await add_user(session)
        await session.commit()

    token = await login(client)
    response = await client.get("/targets/debt", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    by_name = {d["name"]: d for d in body}
    assert by_name["Working Capital Loan - Test Director"]["repaid_date"] == "2025-10-31"
    assert by_name["SBCI backed term loan"]["repaid_date"] is None
