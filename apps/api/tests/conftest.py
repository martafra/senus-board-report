import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.db import get_db
from app.main import app
from app.models.base import Base

# A separate database from the dev one (docker-compose's `db` service), so tests never touch real
# data. Create it once locally with:
#   docker compose exec db psql -U senus -d senus_board_report -c "CREATE DATABASE senus_board_report_test;"
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://senus:senus@localhost:5432/senus_board_report_test",
)


@pytest_asyncio.fixture
async def session_factory():
    # Function-scoped (not session-scoped): asyncpg connections are bound to the event loop they
    # were created in, and pytest-asyncio gives each test function its own event loop, so a
    # session-scoped engine ends up reused across event loops and errors with "another operation
    # is in progress". Recreating a small engine per test avoids that; the suite is tiny enough
    # that the extra setup/teardown cost doesn't matter.
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(session_factory):
    """An httpx client wired to the real FastAPI app, with the database dependency swapped for the
    test database so requests hit the same isolated schema the test itself can set up/inspect."""

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
