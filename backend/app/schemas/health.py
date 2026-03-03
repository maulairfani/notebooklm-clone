from enum import StrEnum

from pydantic import BaseModel


class HealthStatus(StrEnum):
    healthy = "healthy"
    unhealthy = "unhealthy"


class HealthResponse(BaseModel):
    status: HealthStatus
    database: HealthStatus
