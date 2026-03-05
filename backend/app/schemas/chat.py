import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class ChatCreate(BaseModel):
    title: str | None = None


class ChatResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    notebook_id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ChatDetailResponse(ChatResponse):
    messages: list["MessageResponse"]


class MessageCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message content must not be empty")
        return v


class MessageResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    chat_id: uuid.UUID
    role: str
    content: str
    created_at: datetime
