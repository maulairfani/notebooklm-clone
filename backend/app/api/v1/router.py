from fastapi import APIRouter

from app.api.v1.endpoints import auth, chats, health, notebooks, sources

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(notebooks.router, prefix="/notebooks", tags=["notebooks"])
api_router.include_router(sources.router, prefix="/notebooks", tags=["sources"])
api_router.include_router(chats.router, prefix="/notebooks", tags=["chats"])
