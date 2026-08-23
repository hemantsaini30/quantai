# FILE LOCATION: quantai/apps/ai-service/app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://quantai:quantai_dev_password@localhost:5432/quantai"

    class Config:
        env_file = ".env"


settings = Settings()
