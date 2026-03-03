import os
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.schemas.response import ApiResponse
from app.schemas.source import SourceResponse
from app.services.source_service import (
    create_source,
    delete_source,
    get_source,
    get_sources,
)
from app.workers.tasks import process_source

router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post(
    "/{notebook_id}/sources",
    response_model=ApiResponse[SourceResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_source(
    notebook_id: uuid.UUID,
    file: UploadFile,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[SourceResponse]:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Only PDF files are supported",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="File size exceeds 50MB limit",
        )

    file_name = file.filename or "upload.pdf"

    # Create DB record first to get the source id, then save file using that id
    source = await create_source(
        db,
        notebook_id=notebook_id,
        user_id=current_user.id,
        title=file_name,
        source_type="pdf",
        file_path="",  # temporary, updated below
    )

    upload_dir = os.path.join(settings.UPLOAD_DIR, str(notebook_id), str(source.id))
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file_name)
    with open(file_path, "wb") as f:
        f.write(content)

    source.file_path = file_path
    await db.flush()
    await db.refresh(source)

    process_source.delay(str(source.id))

    return ApiResponse(
        status_code=status.HTTP_202_ACCEPTED,
        message="Source upload accepted, processing started",
        data=SourceResponse.model_validate(source),
    )


@router.get(
    "/{notebook_id}/sources",
    response_model=ApiResponse[list[SourceResponse]],
)
async def list_sources(
    notebook_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[list[SourceResponse]]:
    sources = await get_sources(db, notebook_id=notebook_id, user_id=current_user.id)
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Sources retrieved successfully",
        data=[SourceResponse.model_validate(s) for s in sources],
    )


@router.get(
    "/{notebook_id}/sources/{source_id}",
    response_model=ApiResponse[SourceResponse],
)
async def get_one_source(
    notebook_id: uuid.UUID,
    source_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[SourceResponse]:
    source = await get_source(
        db, source_id=source_id, notebook_id=notebook_id, user_id=current_user.id
    )
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Source retrieved successfully",
        data=SourceResponse.model_validate(source),
    )


@router.delete(
    "/{notebook_id}/sources/{source_id}",
    response_model=ApiResponse[None],
)
async def remove_source(
    notebook_id: uuid.UUID,
    source_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[None]:
    await delete_source(
        db, source_id=source_id, notebook_id=notebook_id, user_id=current_user.id
    )
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Source deleted successfully",
        data=None,
    )
