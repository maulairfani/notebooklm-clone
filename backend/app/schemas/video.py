import uuid
from datetime import datetime

from pydantic import BaseModel


class VideoCreate(BaseModel):
    title: str
    language: str = "id-ID"
    voice_name: str | None = None


class VideoResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    notebook_id: uuid.UUID
    title: str
    status: str
    language: str
    voice_name: str | None
    file_path: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
