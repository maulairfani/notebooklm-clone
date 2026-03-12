import os
import shutil
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.notebook import Notebook
from app.models.podcast import Podcast


async def create_podcast(
    db: AsyncSession,
    notebook_id: uuid.UUID,
    user_id: uuid.UUID,
    language: str,
    format: str = "deep_dive",
    length: str = "default",
    custom_prompt: str | None = None,
    host_voice: str = "Kore",
    guest_voice: str = "Puck",
    test_mode: bool = False,
) -> Podcast:
    notebook = await _get_notebook(db, notebook_id, user_id)
    title = f"Podcast - {notebook.title}"
    podcast = Podcast(
        notebook_id=notebook_id,
        title=title,
        language=language,
        format=format,
        length=length,
        custom_prompt=custom_prompt,
        host_voice=host_voice,
        guest_voice=guest_voice,
        test_mode=test_mode,
        status="pending",
    )
    db.add(podcast)
    await db.flush()
    await db.refresh(podcast)
    return podcast


async def get_podcasts(
    db: AsyncSession, notebook_id: uuid.UUID, user_id: uuid.UUID
) -> list[Podcast]:
    await _get_notebook(db, notebook_id, user_id)
    result = await db.execute(
        select(Podcast)
        .where(Podcast.notebook_id == notebook_id)
        .order_by(Podcast.created_at.desc())
    )
    return list(result.scalars().all())


async def get_podcast(
    db: AsyncSession,
    podcast_id: uuid.UUID,
    notebook_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Podcast:
    await _get_notebook(db, notebook_id, user_id)
    result = await db.execute(
        select(Podcast).where(
            Podcast.id == podcast_id, Podcast.notebook_id == notebook_id
        )
    )
    podcast = result.scalar_one_or_none()
    if podcast is None:
        raise NotFoundError("Podcast not found")
    return podcast


async def delete_podcast(
    db: AsyncSession,
    podcast_id: uuid.UUID,
    notebook_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    podcast = await get_podcast(db, podcast_id, notebook_id, user_id)
    if podcast.file_path:
        podcast_dir = os.path.dirname(podcast.file_path)
        if os.path.exists(podcast_dir):
            shutil.rmtree(podcast_dir, ignore_errors=True)
    await db.delete(podcast)
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
