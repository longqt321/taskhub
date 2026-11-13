"""Test profile của user đang đăng nhập."""

from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import User
from tests.conftest import USER_PAYLOAD, login_user, register_user

ME_URL = "/api/v1/users/me"


async def test_get_me_requires_token(client: AsyncClient) -> None:
    response = await client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


async def test_get_me_rejects_bad_token(client: AsyncClient) -> None:
    response = await client.get(ME_URL, headers={"Authorization": "Bearer nonsense"})

    assert response.status_code == 401


async def test_get_me_returns_profile(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.get(ME_URL, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == USER_PAYLOAD["email"]
    assert body["full_name"] == USER_PAYLOAD["full_name"]


async def test_update_full_name(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.patch(ME_URL, headers=auth_headers, json={"full_name": "New Name"})

    assert response.status_code == 200
    assert response.json()["full_name"] == "New Name"


async def test_change_password_then_login_with_new_one(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.patch(
        ME_URL,
        headers=auth_headers,
        json={"current_password": USER_PAYLOAD["password"], "password": "newsecret123"},
    )
    assert response.status_code == 200

    old = await client.post(
        "/api/v1/auth/login",
        json={"email": USER_PAYLOAD["email"], "password": USER_PAYLOAD["password"]},
    )
    new = await client.post(
        "/api/v1/auth/login",
        json={"email": USER_PAYLOAD["email"], "password": "newsecret123"},
    )

    assert old.status_code == 401
    assert new.status_code == 200


async def test_change_password_rejects_wrong_current(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.patch(
        ME_URL,
        headers=auth_headers,
        json={"current_password": "wrong-one", "password": "newsecret123"},
    )

    assert response.status_code == 401


async def test_change_password_requires_current(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.patch(ME_URL, headers=auth_headers, json={"password": "newsecret123"})

    assert response.status_code == 422


async def test_update_me_rejects_null_full_name(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.patch(ME_URL, headers=auth_headers, json={"full_name": None})

    assert response.status_code == 422


async def test_inactive_user_cannot_use_token(
    client: AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await register_user(client)
    tokens = await login_user(client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # tắt tài khoản trực tiếp trong DB, mô phỏng admin khoá user
    async with session_factory() as session:
        await session.execute(update(User).values(is_active=False))
        await session.commit()

    response = await client.get(ME_URL, headers=headers)

    assert response.status_code == 401
