import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, DbSession
from app.schemas.podcast import PodcastCreate, PodcastResponse
from app.schemas.response import ApiResponse
from app.services.podcast_service import (
    create_podcast,
    delete_podcast,
    get_podcast,
    get_podcasts,
)
from app.workers.tasks import generate_podcast

router = APIRouter()


@router.post(
    "/{notebook_id}/podcasts",
    response_model=ApiResponse[PodcastResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_podcast_endpoint(
    notebook_id: uuid.UUID,
    body: PodcastCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[PodcastResponse]:
    podcast = await create_podcast(
        db,
        notebook_id=notebook_id,
        user_id=current_user.id,
        language=body.language,
        format=body.format,
        length=body.length,
        custom_prompt=body.custom_prompt,
        host_voice=body.host_voice,
        guest_voice=body.guest_voice,
        test_mode=body.test_mode,
    )
    generate_podcast.delay(str(podcast.id))
    return ApiResponse(
        status_code=status.HTTP_202_ACCEPTED,
        message="Podcast generation accepted, processing started",
        data=PodcastResponse.model_validate(podcast),
    )


@router.get(
    "/{notebook_id}/podcasts",
    response_model=ApiResponse[list[PodcastResponse]],
)
async def list_podcasts(
    notebook_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[list[PodcastResponse]]:
    podcasts = await get_podcasts(db, notebook_id=notebook_id, user_id=current_user.id)
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Podcasts retrieved successfully",
        data=[PodcastResponse.model_validate(p) for p in podcasts],
    )


@router.get(
    "/{notebook_id}/podcasts/{podcast_id}",
    response_model=ApiResponse[PodcastResponse],
)
async def get_one_podcast(
    notebook_id: uuid.UUID,
    podcast_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[PodcastResponse]:
    podcast = await get_podcast(
        db, podcast_id=podcast_id, notebook_id=notebook_id, user_id=current_user.id
    )
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Podcast retrieved successfully",
        data=PodcastResponse.model_validate(podcast),
    )


@router.get("/{notebook_id}/podcasts/{podcast_id}/download")
async def download_podcast(
    notebook_id: uuid.UUID,
    podcast_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> FileResponse:
    podcast = await get_podcast(
        db, podcast_id=podcast_id, notebook_id=notebook_id, user_id=current_user.id
    )
    if podcast.status != "ready" or not podcast.file_path:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Podcast is not ready for download",
        )
    return FileResponse(
        path=podcast.file_path,
        media_type="audio/wav",
        filename=f"{podcast.title}.wav",
    )


@router.delete(
    "/{notebook_id}/podcasts/{podcast_id}",
    response_model=ApiResponse[None],
)
async def remove_podcast(
    notebook_id: uuid.UUID,
    podcast_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[None]:
    await delete_podcast(
        db, podcast_id=podcast_id, notebook_id=notebook_id, user_id=current_user.id
    )
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Podcast deleted successfully",
        data=None,
    )
