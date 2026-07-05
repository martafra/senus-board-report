from app.core.config import Settings


def test_database_url_normalises_bare_postgres_scheme_to_asyncpg():
    settings = Settings(database_url="postgres://user:pass@host:5432/dbname")
    assert settings.database_url == "postgresql+asyncpg://user:pass@host:5432/dbname"


def test_database_url_normalises_bare_postgresql_scheme_to_asyncpg():
    settings = Settings(database_url="postgresql://user:pass@host:5432/dbname")
    assert settings.database_url == "postgresql+asyncpg://user:pass@host:5432/dbname"


def test_database_url_left_untouched_when_already_asyncpg():
    settings = Settings(database_url="postgresql+asyncpg://user:pass@host:5432/dbname")
    assert settings.database_url == "postgresql+asyncpg://user:pass@host:5432/dbname"
