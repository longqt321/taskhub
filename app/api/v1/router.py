"""Aggregate router for API v1."""

from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/health", tags=["health"], summary="Service health check")
async def health_check() -> dict[str, str]:
    """Report basic service liveness."""
    return {"status": "ok"}
