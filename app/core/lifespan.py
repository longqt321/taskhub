"""Chạy lúc app start và shutdown."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import create_engine, create_session_factory
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

    engine = create_engine(settings.database_url)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    logger.info("Database engine created")

    # Day 5: tạo pool Redis ở đây.

    yield

    await engine.dispose()
    # Day 5: đóng pool Redis.
    logger.info("Shutting down %s", settings.app_name)
