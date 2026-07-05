import asyncio
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import insights as ai_insights
from app.models import AIInsight
from app.schemas.metrics import PeriodMetrics


async def get_or_generate_insight(
    session: AsyncSession,
    section_key: str,
    metrics: list[PeriodMetrics],
    *,
    force_regenerate: bool = False,
    generate_fn: Callable[[str, list[PeriodMetrics]], str] | None = None,
) -> AIInsight:
    """Returns the cached insight for a section, generating (and caching) one if there isn't one
    yet, or if force_regenerate is set. generate_fn defaults to the real Gemini call
    (app.ai.insights.generate_insight, looked up here at call time so tests can monkeypatch the
    module function) but can also be injected directly for unit tests that would rather not patch
    module state."""
    existing = await session.scalar(select(AIInsight).where(AIInsight.section_key == section_key))
    if existing is not None and not force_regenerate:
        return existing

    # Commit here to release this connection's transaction before the slow, blocking call to
    # Gemini below: holding a transaction open for the seconds that call takes leaves the
    # connection "idle in transaction" and can exhaust the pool for unrelated requests (this
    # actually happened during manual testing). Also run the call in a worker thread so its
    # blocking network I/O doesn't stall the whole (single-threaded) event loop for other
    # requests in the meantime.
    await session.commit()
    fn = generate_fn if generate_fn is not None else ai_insights.generate_insight
    content = await asyncio.to_thread(fn, section_key, metrics)
    now = datetime.now(timezone.utc)

    if existing is not None:
        existing.content = content
        existing.model = ai_insights.MODEL
        existing.generated_at = now
        existing.prompt_version = ai_insights.PROMPT_VERSION
        insight = existing
    else:
        insight = AIInsight(
            section_key=section_key,
            period_id=None,
            content=content,
            model=ai_insights.MODEL,
            generated_at=now,
            prompt_version=ai_insights.PROMPT_VERSION,
        )
        session.add(insight)

    await session.commit()
    await session.refresh(insight)
    return insight
