import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.notebook import Notebook


async def create_notebook(db: AsyncSession, user_id: uuid.UUID, title: str) -> Notebook:
    notebook = Notebook(title=title, user_id=user_id)
    db.add(notebook)
    await db.flush()
    await db.refresh(notebook)
    return notebook


async def get_notebooks(db: AsyncSession, user_id: uuid.UUID) -> list[Notebook]:
    result = await db.execute(
        select(Notebook).where(Notebook.user_id == user_id).order_by(Notebook.created_at.desc())
    )
    return list(result.scalars().all())


async def get_notebook(db: AsyncSession, notebook_id: uuid.UUID, user_id: uuid.UUID) -> Notebook:
    result = await db.execute(
        select(Notebook).where(Notebook.id == notebook_id, Notebook.user_id == user_id)
    )
    notebook = result.scalar_one_or_none()
    if notebook is None:
        raise NotFoundError("Notebook not found")
    return notebook


async def update_notebook(
    db: AsyncSession, notebook_id: uuid.UUID, user_id: uuid.UUID, title: str
) -> Notebook:
    notebook = await get_notebook(db, notebook_id, user_id)
    notebook.title = title
    await db.flush()
    await db.refresh(notebook)
    return notebook


async def delete_notebook(
    db: AsyncSession, notebook_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    notebook = await get_notebook(db, notebook_id, user_id)
    await db.delete(notebook)
    await db.flush()
