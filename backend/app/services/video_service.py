import os
import shutil
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.notebook import Notebook
from app.models.video import Video


_DEFAULT_VOICE_NAME = "Kore"


async def create_video(
    db: AsyncSession,
    notebook_id: uuid.UUID,
    user_id: uuid.UUID,
    language: str,
) -> Video:
    notebook = await _get_notebook(db, notebook_id, user_id)
    title = f"Video - {notebook.title}"
    video = Video(
        notebook_id=notebook_id,
        title=title,
        language=language,
        voice_name=_DEFAULT_VOICE_NAME,
        status="pending",
    )
    db.add(video)
    await db.flush()
    await db.refresh(video)
    return video


async def get_videos(
    db: AsyncSession, notebook_id: uuid.UUID, user_id: uuid.UUID
) -> list[Video]:
    await _get_notebook(db, notebook_id, user_id)
    result = await db.execute(
        select(Video)
        .where(Video.notebook_id == notebook_id)
        .order_by(Video.created_at.desc())
    )
    return list(result.scalars().all())


async def get_video(
    db: AsyncSession,
    video_id: uuid.UUID,
    notebook_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Video:
    await _get_notebook(db, notebook_id, user_id)
    result = await db.execute(
        select(Video).where(Video.id == video_id, Video.notebook_id == notebook_id)
    )
    video = result.scalar_one_or_none()
    if video is None:
        raise NotFoundError("Video not found")
    return video


async def delete_video(
    db: AsyncSession,
    video_id: uuid.UUID,
    notebook_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    video = await get_video(db, video_id, notebook_id, user_id)
    # Remove output directory if it exists
    if video.file_path:
        video_dir = os.path.dirname(video.file_path)
        if os.path.exists(video_dir):
            shutil.rmtree(video_dir, ignore_errors=True)
    await db.delete(video)
    await db.flush()


async def _get_notebook(
    db: AsyncSession, notebook_id: uuid.UUID, user_id: uuid.UUID
) -> Notebook:
    result = await db.execute(
        select(Notebook).where(
            Notebook.id == notebook_id, Notebook.user_id == user_id
        )
    )
    notebook = result.scalar_one_or_none()
    if notebook is None:
        raise NotFoundError("Notebook not found")
    return notebook
