from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.schemas.response import ApiResponse
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_user,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=ApiResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(body: RegisterRequest, db: DbSession) -> ApiResponse[TokenResponse]:
    user = await create_user(db, email=body.email, password=body.password)
    token = create_access_token({"sub": str(user.id)})
    return ApiResponse(
        status_code=status.HTTP_201_CREATED,
        message="User registered successfully",
        data=TokenResponse(access_token=token),
    )


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(body: LoginRequest, db: DbSession) -> ApiResponse[TokenResponse]:
    user = await authenticate_user(db, email=body.email, password=body.password)
    token = create_access_token({"sub": str(user.id)})
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="Login successful",
        data=TokenResponse(access_token=token),
    )


@router.get("/me", response_model=ApiResponse[UserResponse])
async def me(current_user: CurrentUser) -> ApiResponse[UserResponse]:
    return ApiResponse(
        status_code=status.HTTP_200_OK,
        message="User retrieved successfully",
        data=UserResponse.model_validate(current_user),
    )
