"""Application lifespan: startup and shutdown hooks."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup/shutdown logic around the application's lifetime."""
    settings = get_settings()
    logger.info(
        "Starting %s v%s (environment=%s, debug=%s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
        settings.debug,
    )

    # Day 2: create the SQLAlchemy async engine and session factory here.
    # Day 5: create the Redis connection pool here.

    yield

    # Day 2: dispose the database engine here.
    # Day 5: close the Redis connection pool here.
    logger.info("Shutting down %s", settings.app_name)
