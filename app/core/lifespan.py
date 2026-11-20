"""Chạy lúc app start và shutdown."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

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

    redis_client: Redis | None = None
    if settings.redis_url:
        redis_client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=1.0,
            socket_timeout=1.0,
        )
        logger.info("Redis client created")
    app.state.redis = redis_client

    yield

    if redis_client is not None:
        await redis_client.aclose()
    await engine.dispose()
    logger.info("Shutting down %s", settings.app_name)
