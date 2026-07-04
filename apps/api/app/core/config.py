from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://senus:senus@localhost:5432/senus_board_report"
    anthropic_api_key: str = ""
    jwt_secret: str = "dev-only-change-me"
    jwt_expire_minutes: int = 480
    web_origin: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
