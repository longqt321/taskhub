"""Fixture dùng chung. Test chạy trên database taskhub_test, không đụng DB dev."""

import os

# Phải set trước khi import app để Settings đọc đúng
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://taskhub:taskhub@localhost:5433/taskhub_test"
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-must-be-at-least-32-bytes")

from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.database import create_engine, create_session_factory
from app.main import app
from app.models.user import User, UserRole

TEST_URL = os.environ["DATABASE_URL"]

USER_PAYLOAD = {
    "email": "intern@example.com",
    "full_name": "Intern",
    "password": "secret12345",
}

WORKSPACES_URL = "/api/v1/workspaces"


_ALEMBIC_CFG = Config("alembic.ini")


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations() -> Iterator[None]:
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
        await conn.execute(
            text(
                "TRUNCATE TABLE task_labels, comments, labels, tasks, projects, "
                "workspace_members, workspaces, refresh_tokens, users RESTART IDENTITY CASCADE"
            )
        )
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


async def login_headers(client: AsyncClient, email: str) -> dict[str, str]:
    tokens = await login_user(client, email=email)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Đăng ký rồi đăng nhập, trả về header Authorization."""
    await register_user(client)
    tokens = await login_user(client)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
async def other_user(client: AsyncClient) -> dict[str, Any]:
    """User thứ hai đã đăng ký, dùng khi chỉ cần user tồn tại (ví dụ để mời vào workspace)."""
    return await register_user(client, email="other@example.com", full_name="Other")


@pytest.fixture
async def other_headers(client: AsyncClient, other_user: dict[str, Any]) -> dict[str, str]:
    """Header của user thứ hai, dùng để kiểm tra phân quyền."""
    return await login_headers(client, "other@example.com")


async def promote_to_admin(session_factory: async_sessionmaker[AsyncSession], email: str) -> None:
    """Đổi role trực tiếp trong DB, vì register không cho client tự chọn role."""
    async with session_factory() as session:
        await session.execute(update(User).where(User.email == email).values(role=UserRole.ADMIN))
        await session.commit()


@pytest.fixture
async def admin_headers(
    client: AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> dict[str, str]:
    await register_user(client, email="admin@example.com", full_name="Admin")
    await promote_to_admin(session_factory, "admin@example.com")
    return await login_headers(client, "admin@example.com")


async def create_workspace(
    client: AsyncClient, headers: dict[str, str], name: str = "Team"
) -> dict[str, Any]:
    response = await client.post(WORKSPACES_URL, json={"name": name}, headers=headers)
    assert response.status_code == 201, response.text
    return dict(response.json())


async def create_project(
    client: AsyncClient, headers: dict[str, str], workspace_id: str, name: str = "Backlog"
) -> dict[str, Any]:
    response = await client.post(
        f"{WORKSPACES_URL}/{workspace_id}/projects", json={"name": name}, headers=headers
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


async def invite_member(
    client: AsyncClient,
    headers: dict[str, str],
    workspace_id: str,
    email: str,
    role: str = "VIEWER",
) -> dict[str, Any]:
    response = await client.post(
        f"{WORKSPACES_URL}/{workspace_id}/members",
        json={"email": email, "role": role},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return dict(response.json())


@pytest.fixture
async def workspace(client: AsyncClient, auth_headers: dict[str, str]) -> dict[str, Any]:
    return await create_workspace(client, auth_headers)


@pytest.fixture
async def project(
    client: AsyncClient, auth_headers: dict[str, str], workspace: dict[str, Any]
) -> dict[str, Any]:
    return await create_project(client, auth_headers, workspace["id"])
