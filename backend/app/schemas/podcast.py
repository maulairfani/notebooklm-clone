import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

PodcastFormat = Literal["deep_dive", "brief", "debate", "critique"]
PodcastLength = Literal["short", "default"]


class PodcastCreate(BaseModel):
    language: str = "en-US"
    format: PodcastFormat = "deep_dive"
    length: PodcastLength = "default"
    custom_prompt: str | None = None
    host_voice: str = "Kore"
    guest_voice: str = "Puck"
    test_mode: bool = False


class PodcastResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    notebook_id: uuid.UUID
    title: str
    status: str
    language: str
    format: str
    length: str
    custom_prompt: str | None
    host_voice: str
    guest_voice: str
    test_mode: bool
    file_path: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
