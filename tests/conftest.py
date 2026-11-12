"""Fixtures dùng chung. Test chạy trên database taskhub_test, không đụng DB dev."""

import os

# Phải set trước khi import app để Settings đọc đúng URL test
os.environ["DATABASE_URL"] = "postgresql+asyncpg://taskhub:taskhub@localhost:5433/taskhub_test"

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import create_engine, create_session_factory
from app.main import app
from app.models.item import Base

TEST_URL = os.environ["DATABASE_URL"]


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    engine = create_engine(TEST_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        yield http_client

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
