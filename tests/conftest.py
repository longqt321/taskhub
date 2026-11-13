"""Fixtures dùng chung. Test chạy trên database taskhub_test, không đụng DB dev."""

import os

# Phải set trước khi import app để Settings đọc đúng
os.environ["DATABASE_URL"] = "postgresql+asyncpg://taskhub:taskhub@localhost:5433/taskhub_test"
os.environ["SECRET_KEY"] = "test-secret-key-must-be-at-least-32-bytes"

from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.database import create_engine, create_session_factory
from app.main import app
from app.models import Base

TEST_URL = os.environ["DATABASE_URL"]

USER_PAYLOAD = {
    "email": "intern@example.com",
    "full_name": "Intern",
    "password": "secret12345",
}


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    test_engine = create_engine(TEST_URL)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return create_session_factory(engine)


@pytest.fixture
async def client(
    engine: AsyncEngine, session_factory: async_sessionmaker[AsyncSession]
) -> AsyncIterator[AsyncClient]:
    app.state.engine = engine
    app.state.session_factory = session_factory
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        yield http_client


async def register_user(client: AsyncClient, **overrides: Any) -> dict[str, Any]:
    payload = {**USER_PAYLOAD, **overrides}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return payload


async def login_user(client: AsyncClient, **overrides: Any) -> dict[str, Any]:
    payload = {**USER_PAYLOAD, **overrides}
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert response.status_code == 200, response.text
    return dict(response.json())


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Đăng ký rồi đăng nhập, trả về header Authorization."""
    await register_user(client)
    tokens = await login_user(client)
    return {"Authorization": f"Bearer {tokens['access_token']}"}
