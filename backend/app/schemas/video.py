import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

VideoStructure = Literal["comprehensive", "bite_sized"]
VideoVisualStyle = Literal[
    "white_board", "kawaii", "anime", "water_color", "retro_print", "heritage", "paper_craft"
]


class VideoCreate(BaseModel):
    language: str = "id-ID"
    structure: VideoStructure = "comprehensive"
    visual_style: VideoVisualStyle = "white_board"
    custom_prompt: str | None = None
    test_mode: bool = False
    decorate_slides: bool = True


class VideoResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    notebook_id: uuid.UUID
    title: str
    status: str
    language: str
    structure: str
    visual_style: str
    custom_prompt: str | None
    voice_name: str | None
    test_mode: bool
    decorate_slides: bool
    file_path: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
