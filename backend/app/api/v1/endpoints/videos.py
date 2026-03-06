import uuid

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.schemas.response import ApiResponse
from app.schemas.video import VideoCreate, VideoResponse
from app.services.video_service import (
    create_video,
    delete_video,
    get_video,
    get_videos,
)
from app.workers.tasks import generate_video

router = APIRouter()


@router.post(
    "/{notebook_id}/videos",
    response_model=ApiResponse[VideoResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_video_endpoint(
    notebook_id: uuid.UUID,
    body: VideoCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[VideoResponse]:
    video = await create_video(
        db,
        notebook_id=notebook_id,
        user_id=current_user.id,
        language=body.language,
    )
    generate_video.delay(str(video.id))
    return ApiResponse(
        status_code=status.HTTP_202_ACCEPTED,
        message="Video generation accepted, processing started",
        data=VideoResponse.model_validate(video),
    )


@router.get(
    "/{notebook_id}/videos",
    response_model=ApiResponse[list[VideoResponse]],
)
async def list_videos(
    notebook_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[list[VideoResponse]]:
    videos = await get_videos(db, notebook_id=notebook_id, user_id=current_user.id)
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Videos retrieved successfully",
        data=[VideoResponse.model_validate(v) for v in videos],
    )


@router.get(
    "/{notebook_id}/videos/{video_id}",
    response_model=ApiResponse[VideoResponse],
)
async def get_one_video(
    notebook_id: uuid.UUID,
    video_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[VideoResponse]:
    video = await get_video(
        db, video_id=video_id, notebook_id=notebook_id, user_id=current_user.id
    )
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Video retrieved successfully",
        data=VideoResponse.model_validate(video),
    )


@router.get("/{notebook_id}/videos/{video_id}/download")
async def download_video(
    notebook_id: uuid.UUID,
    video_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> FileResponse:
    video = await get_video(
        db, video_id=video_id, notebook_id=notebook_id, user_id=current_user.id
    )
    if video.status != "ready" or not video.file_path:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Video is not ready for download",
        )
    return FileResponse(
        path=video.file_path,
        media_type="video/mp4",
        filename=f"{video.title}.mp4",
    )


@router.delete(
    "/{notebook_id}/videos/{video_id}",
    response_model=ApiResponse[None],
)
async def remove_video(
    notebook_id: uuid.UUID,
    video_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ApiResponse[None]:
    await delete_video(
        db, video_id=video_id, notebook_id=notebook_id, user_id=current_user.id
    )
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Video deleted successfully",
        data=None,
    )
