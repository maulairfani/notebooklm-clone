from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.schemas.health import HealthResponse, HealthStatus
from app.schemas.response import ApiResponse

router = APIRouter()


@router.get("", response_model=ApiResponse[HealthResponse])
async def health_check(db: DbSession) -> ApiResponse[HealthResponse]:
    try:
        await db.execute(text("SELECT 1"))
        db_status = HealthStatus.healthy
    except Exception:
        db_status = HealthStatus.unhealthy

    return ApiResponse(
        status_code=200,
        message="Service is healthy",
        data=HealthResponse(status=HealthStatus.healthy, database=db_status),
    )
