from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

# Re-export for convenience
DbSession = Annotated[AsyncSession, Depends(get_db)]
