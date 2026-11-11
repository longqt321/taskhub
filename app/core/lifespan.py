"""Chạy lúc app start và shutdown."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info(
        "Starting %s v%s (environment=%s, debug=%s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
        settings.debug,
    )

    # Day 2: tạo engine SQLAlchemy ở đây.
    # Day 5: tạo pool Redis ở đây.

    yield

    # Day 2: dispose engine.
    # Day 5: đóng pool Redis.
    logger.info("Shutting down %s", settings.app_name)
