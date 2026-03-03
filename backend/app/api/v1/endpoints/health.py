from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.schemas.health import HealthResponse, HealthStatus

router = APIRouter()


@router.get("", response_model=HealthResponse)
async def health_check(db: DbSession) -> HealthResponse:
    try:
        await db.execute(text("SELECT 1"))
        db_status = HealthStatus.healthy
    except Exception:
        db_status = HealthStatus.unhealthy

    return HealthResponse(
        status=HealthStatus.healthy,
        database=db_status,
    )
