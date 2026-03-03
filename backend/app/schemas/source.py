import uuid
from datetime import datetime

from pydantic import BaseModel


class SourceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    notebook_id: uuid.UUID
    title: str
    source_type: str
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime
