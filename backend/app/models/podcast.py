import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Podcast(Base):
    __tablename__ = "podcasts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    notebook_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="en-US")
    format: Mapped[str] = mapped_column(String(50), nullable=False, default="deep_dive")
    length: Mapped[str] = mapped_column(String(50), nullable=False, default="default")
    custom_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    host_voice: Mapped[str] = mapped_column(String(50), nullable=False, default="Kore")
    guest_voice: Mapped[str] = mapped_column(String(50), nullable=False, default="Puck")
    test_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
