"""Router gom các endpoint của API v1."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, tasks, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(tasks.router)


@api_router.get("/health", tags=["health"], summary="Service health check")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
