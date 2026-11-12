"""Fixture dùng chung. Test chạy trên database taskhub_test, không đụng DB dev."""

import os

# Phải set trước khi import app để Settings đọc đúng URL test
os.environ["DATABASE_URL"] = "postgresql+asyncpg://taskhub:taskhub@localhost:5433/taskhub_test"

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.database import create_engine, create_session_factory
from app.main import app
from app.models import Base

TEST_URL = os.environ["DATABASE_URL"]


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    engine = create_engine(TEST_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    # Không chạy lifespan trong test nên gán thẳng engine và session factory vào app
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    # raise_app_exceptions=False để bắt được response 500 thay vì exception ném ra
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE tasks"))
