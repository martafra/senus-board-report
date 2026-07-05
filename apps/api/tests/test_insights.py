from unittest.mock import patch

from google.genai.errors import ClientError
from sqlalchemy import select

from app.ai import insights as ai_insights
from app.models import AIInsight
from app.services.insights import get_or_generate_insight
from tests.factories import add_annual_period, add_user, login


async def test_generates_and_caches_a_new_insight(session_factory):
    calls: list[str] = []

    def fake_generate(section_key, metrics):
        calls.append(section_key)
        return "Revenue grew steadily this year."

    async with session_factory() as session:
        insight = await get_or_generate_insight(
            session, "profitability", metrics=[], generate_fn=fake_generate
        )

    assert insight.content == "Revenue grew steadily this year."
    assert insight.section_key == "profitability"
    assert len(calls) == 1

    async with session_factory() as session:
        stored = await session.scalar(
            select(AIInsight).where(AIInsight.section_key == "profitability")
        )
        assert stored is not None
        assert stored.content == "Revenue grew steadily this year."


async def test_returns_cached_insight_without_calling_generate_fn_again(session_factory):
    calls: list[str] = []

    def fake_generate(section_key, metrics):
        calls.append(section_key)
        return f"Generated #{len(calls)}"

    async with session_factory() as session:
        await get_or_generate_insight(session, "profitability", metrics=[], generate_fn=fake_generate)

    async with session_factory() as session:
        second = await get_or_generate_insight(
            session, "profitability", metrics=[], generate_fn=fake_generate
        )

    assert len(calls) == 1  # not called a second time
    assert second.content == "Generated #1"


async def test_force_regenerate_calls_generate_fn_again_and_updates_content(session_factory):
    calls: list[str] = []

    def fake_generate(section_key, metrics):
        calls.append(section_key)
        return f"Generated #{len(calls)}"

    async with session_factory() as session:
        await get_or_generate_insight(session, "profitability", metrics=[], generate_fn=fake_generate)

    async with session_factory() as session:
        second = await get_or_generate_insight(
            session, "profitability", metrics=[], generate_fn=fake_generate, force_regenerate=True
        )

    assert len(calls) == 2
    assert second.content == "Generated #2"


async def test_looks_up_generate_insight_at_call_time_so_monkeypatching_works(session_factory, monkeypatch):
    monkeypatch.setattr(ai_insights, "generate_insight", lambda section, metrics: "Patched content")

    async with session_factory() as session:
        insight = await get_or_generate_insight(session, "profitability", metrics=[])

    assert insight.content == "Patched content"


async def test_insight_endpoint_requires_auth(client):
    response = await client.get("/insights/profitability")
    assert response.status_code == 401


async def test_insight_endpoint_returns_generated_content(client, session_factory):
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

    with patch.object(ai_insights, "generate_insight", return_value="A short board commentary."):
        response = await client.get(
            "/insights/profitability", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["content"] == "A short board commentary."
    assert body["section_key"] == "profitability"


async def test_insight_endpoint_unknown_section_returns_404(client, session_factory):
    async with session_factory() as session:
        await add_user(session)
    token = await login(client)

    response = await client.get(
        "/insights/not-a-real-section", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 404


async def test_regenerate_endpoint_produces_new_content(client, session_factory):
    async with session_factory() as session:
        await add_annual_period(session, label="FY2025", fiscal_year=2025, facts={"revenue": 1.0})
        await add_user(session)
    token = await login(client)
    headers = {"Authorization": f"Bearer {token}"}

    with patch.object(ai_insights, "generate_insight", return_value="First version."):
        first = await client.get("/insights/profitability", headers=headers)
    assert first.json()["content"] == "First version."

    with patch.object(ai_insights, "generate_insight", return_value="Regenerated version."):
        second = await client.post("/insights/profitability/regenerate", headers=headers)
    assert second.json()["content"] == "Regenerated version."


async def test_endpoint_returns_a_clean_error_when_the_ai_service_fails(client, session_factory):
    # Reproduces a real failure seen in manual testing: the Gemini free tier's request quota was
    # exceeded, which raised google.genai.errors.ClientError. This should surface as a clear 503,
    # not a bare 500 with an internal traceback.
    async with session_factory() as session:
        await add_annual_period(session, label="FY2025", fiscal_year=2025, facts={"revenue": 1.0})
        await add_user(session)
    token = await login(client)

    quota_error = ClientError(429, {"error": {"message": "quota exceeded, retry in 12s"}})
    with patch.object(ai_insights, "generate_insight", side_effect=quota_error):
        response = await client.get(
            "/insights/profitability", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 503
    assert "quota exceeded" in response.json()["detail"]
