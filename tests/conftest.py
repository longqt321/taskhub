"""Fixture dùng chung. Test chạy qua migration Alembic trên DB test, không đụng DB dev."""

import os

from alembic import command
from alembic.config import Config

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://taskhub:taskhub@localhost:5433/taskhub_test"
)

from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from app.core.database import create_engine, create_session_factory
from app.main import app

TEST_URL = os.environ["DATABASE_URL"]
_ALEMBIC_CFG = Config("alembic.ini")


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations() -> Iterator[None]:
    """Dựng schema bằng migration thật một lần cho cả phiên test."""
    command.downgrade(_ALEMBIC_CFG, "base")
    command.upgrade(_ALEMBIC_CFG, "head")
    try:
        yield
    finally:
        command.downgrade(_ALEMBIC_CFG, "base")


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    test_engine = create_engine(TEST_URL, echo=False)
    async with test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE tasks RESTART IDENTITY CASCADE"))
    yield test_engine
    await test_engine.dispose()


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return create_session_factory(engine)


@pytest.fixture
async def client(
    engine: AsyncEngine, session_factory: async_sessionmaker[AsyncSession]
) -> AsyncIterator[AsyncClient]:
    # Không chạy lifespan trong test nên gán thẳng engine và session factory vào app
    app.state.engine = engine
    app.state.session_factory = session_factory
    # raise_app_exceptions=False để bắt được response 500 thay vì exception ném ra
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


async def create_sample_task(
    client: AsyncClient, title: str = "Write tests", description: str | None = "day 2"
) -> dict[str, Any]:
    response = await client.post("/api/v1/tasks", json={"title": title, "description": description})
    assert response.status_code == 201, response.text
    return dict(response.json())
