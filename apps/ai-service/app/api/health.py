# FILE LOCATION: quantai/apps/ai-service/app/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Proves ai-service is running AND can reach Postgres.
    Called by apps/api's /api/health endpoint to complete the
    full web -> api -> ai-service -> postgres chain check.
    """
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:  # noqa: BLE001 - deliberately broad for a health check
        db_status = f"error: {exc}"

    return {"status": "ok", "postgres": db_status}
