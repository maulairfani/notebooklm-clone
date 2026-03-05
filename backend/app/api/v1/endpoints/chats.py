import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.chat import (
    ChatCreate,
    ChatDetailResponse,
    ChatResponse,
    MessageCreate,
    MessageResponse,
)
from app.schemas.response import ApiResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.post(
    "/{notebook_id}/chats",
    response_model=ApiResponse[ChatResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create(
    notebook_id: uuid.UUID,
    body: ChatCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[ChatResponse]:
    service = ChatService(db)
    chat = await service.create_chat(
        notebook_id=notebook_id, user_id=current_user.id, title=body.title
    )
    return ApiResponse(
        status_code=status.HTTP_201_CREATED,
        message="Chat created successfully",
        data=ChatResponse.model_validate(chat),
    )


@router.get(
    "/{notebook_id}/chats",
    response_model=ApiResponse[list[ChatResponse]],
)
async def list_chats(
    notebook_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[list[ChatResponse]]:
    service = ChatService(db)
    chats = await service.get_chats(notebook_id=notebook_id, user_id=current_user.id)
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Chats retrieved successfully",
        data=[ChatResponse.model_validate(c) for c in chats],
    )


@router.get(
    "/{notebook_id}/chats/{chat_id}",
    response_model=ApiResponse[ChatDetailResponse],
)
async def get_one(
    notebook_id: uuid.UUID,
    chat_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[ChatDetailResponse]:
    service = ChatService(db)
    chat = await service.get_chat(
        chat_id=chat_id, notebook_id=notebook_id, user_id=current_user.id
    )
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Chat retrieved successfully",
        data=ChatDetailResponse.model_validate(chat),
    )


@router.post(
    "/{notebook_id}/chats/{chat_id}/messages",
    response_model=ApiResponse[MessageResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    notebook_id: uuid.UUID,
    chat_id: uuid.UUID,
    body: MessageCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[MessageResponse]:
    service = ChatService(db)
    message = await service.send_message(
        chat_id=chat_id,
        notebook_id=notebook_id,
        user_id=current_user.id,
        content=body.content,
    )
    return ApiResponse(
        status_code=status.HTTP_201_CREATED,
        message="Message sent successfully",
        data=MessageResponse.model_validate(message),
    )


@router.delete(
    "/{notebook_id}/chats/{chat_id}",
    response_model=ApiResponse[None],
)
async def delete(
    notebook_id: uuid.UUID,
    chat_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[None]:
    service = ChatService(db)
    await service.delete_chat(
        chat_id=chat_id, notebook_id=notebook_id, user_id=current_user.id
    )
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Chat deleted successfully",
        data=None,
    )
