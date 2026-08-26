# FILE LOCATION: quantai/apps/ai-service/app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://quantai:quantai_dev_password@localhost:5432/quantai"

    # Twelve Data — free tier, 5 keys rotated to spread out rate limits.
    # Optional (default None) so the app still starts if not all are set.
    twelve_api_key1: str | None = None
    twelve_api_key2: str | None = None
    twelve_api_key3: str | None = None
    twelve_api_key4: str | None = None
    twelve_api_key5: str | None = None

    # Finnhub — used for US stock symbol search
    finnhub_api_key: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"  # don't hard-fail on any future env vars we haven't
        # explicitly declared yet — safer default than the implicit "forbid"
        # behavior that caused the earlier error.


settings = Settings()