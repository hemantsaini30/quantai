# FILE LOCATION: quantai/apps/ai-service/app/core/db.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings

# Single shared async engine, read from the SAME Postgres instance as apps/api.
# ai-service reads portfolios/holdings/price_history and writes optimization_runs/
# simulation_runs/backtest_runs (see docs/architecture for the full table list).
engine = create_async_engine(settings.database_url, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """FastAPI dependency — yields a DB session per request."""
    async with AsyncSessionLocal() as session:
        yield session
