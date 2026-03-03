import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class NotebookCreate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title must not be empty")
        return v


class NotebookUpdate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title must not be empty")
        return v


class NotebookResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
