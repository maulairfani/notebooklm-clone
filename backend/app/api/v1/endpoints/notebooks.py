import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.notebook import NotebookCreate, NotebookResponse, NotebookUpdate
from app.schemas.response import ApiResponse
from app.services.notebook_service import (
    create_notebook,
    delete_notebook,
    get_notebook,
    get_notebooks,
    update_notebook,
)

router = APIRouter()


@router.post("", response_model=ApiResponse[NotebookResponse], status_code=status.HTTP_201_CREATED)
async def create(
    body: NotebookCreate, db: DbSession, current_user: CurrentUser
) -> ApiResponse[NotebookResponse]:
    notebook = await create_notebook(db, user_id=current_user.id, title=body.title)
    return ApiResponse(
        status_code=status.HTTP_201_CREATED,
        message="Notebook created successfully",
        data=NotebookResponse.model_validate(notebook),
    )


@router.get("", response_model=ApiResponse[list[NotebookResponse]])
async def list_notebooks(
    db: DbSession, current_user: CurrentUser
) -> ApiResponse[list[NotebookResponse]]:
    notebooks = await get_notebooks(db, user_id=current_user.id)
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Notebooks retrieved successfully",
        data=[NotebookResponse.model_validate(n) for n in notebooks],
    )


@router.get("/{notebook_id}", response_model=ApiResponse[NotebookResponse])
async def get_one(
    notebook_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> ApiResponse[NotebookResponse]:
    notebook = await get_notebook(db, notebook_id=notebook_id, user_id=current_user.id)
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Notebook retrieved successfully",
        data=NotebookResponse.model_validate(notebook),
    )


@router.put("/{notebook_id}", response_model=ApiResponse[NotebookResponse])
async def update(
    notebook_id: uuid.UUID, body: NotebookUpdate, db: DbSession, current_user: CurrentUser
) -> ApiResponse[NotebookResponse]:
    notebook = await update_notebook(
        db, notebook_id=notebook_id, user_id=current_user.id, title=body.title
    )
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Notebook updated successfully",
        data=NotebookResponse.model_validate(notebook),
    )


@router.delete("/{notebook_id}", response_model=ApiResponse[None])
async def delete(
    notebook_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> ApiResponse[None]:
    await delete_notebook(db, notebook_id=notebook_id, user_id=current_user.id)
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Notebook deleted successfully",
        data=None,
    )
