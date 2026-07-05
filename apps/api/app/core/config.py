from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_repo_root_env() -> Path | None:
    """Locate the repo-root .env for local (non-docker) runs, via this file's own location
    (apps/api/app/core/config.py -> core -> app -> api -> apps -> repo root). Inside the Docker
    image this file only has 3 parent directories (docker-compose mounts apps/api at /app, so this
    file lives at /app/app/core/config.py), and there's no local .env to find there anyway:
    docker-compose's `env_file:` directive already injects those variables into the container's
    real environment, which pydantic-settings reads regardless of env_file."""
    here = Path(__file__).resolve()
    try:
        candidate = here.parents[4] / ".env"
    except IndexError:
        return None
    return candidate if candidate.exists() else None


REPO_ROOT_ENV = _find_repo_root_env()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT_ENV, extra="ignore")

    database_url: str = "postgresql+asyncpg://senus:senus@localhost:5432/senus_board_report"
    gemini_api_key: str = ""
    jwt_secret: str = "dev-only-change-me"
    jwt_expire_minutes: int = 480
    web_origin: str = "http://localhost:5173"
    demo_user_email: str = ""
    demo_user_password: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
