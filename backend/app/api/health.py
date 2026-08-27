"""GET /health — liveness + DB readiness check."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db

router = APIRouter(tags=["system"])


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    """Returns API status and database connectivity status."""
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "degraded"

    return {"status": "ok", "db": db_status}
