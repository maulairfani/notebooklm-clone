import os
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.notebook import Notebook
from app.models.source import Source


async def create_source(
    db: AsyncSession,
    notebook_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
    source_type: str,
    file_path: str,
) -> Source:
    await _get_notebook(db, notebook_id, user_id)
    source = Source(
        notebook_id=notebook_id,
        title=title,
        source_type=source_type,
        file_path=file_path,
        status="pending",
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return source


async def get_sources(
    db: AsyncSession, notebook_id: uuid.UUID, user_id: uuid.UUID
) -> list[Source]:
    # verify notebook ownership
    await _get_notebook(db, notebook_id, user_id)
    result = await db.execute(
        select(Source)
        .where(Source.notebook_id == notebook_id)
        .order_by(Source.created_at.desc())
    )
    return list(result.scalars().all())


async def get_source(
    db: AsyncSession,
    source_id: uuid.UUID,
    notebook_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Source:
    await _get_notebook(db, notebook_id, user_id)
    result = await db.execute(
        select(Source).where(
            Source.id == source_id, Source.notebook_id == notebook_id
        )
    )
    source = result.scalar_one_or_none()
    if source is None:
        raise NotFoundError("Source not found")
    return source


async def delete_source(
    db: AsyncSession,
    source_id: uuid.UUID,
    notebook_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    source = await get_source(db, source_id, notebook_id, user_id)
    # TODO(minor): `os.path.exists` + `os.remove` adalah blocking IO di async context.
    # Ganti ke `await asyncio.to_thread(os.remove, source.file_path)` setelah cek exists.
    if source.file_path and os.path.exists(source.file_path):
        os.remove(source.file_path)
    await db.delete(source)
    await db.flush()


async def update_source_status(
    db: AsyncSession,
    source_id: uuid.UUID,
    status: str,
    error_message: str | None = None,
) -> None:
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    if source is None:
        return
    source.status = status
    if error_message is not None:
        source.error_message = error_message
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
