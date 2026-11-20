"""Test profile của user đang đăng nhập và các thao tác admin trên user."""

from typing import Any

from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models import User
from tests.conftest import (
    USER_PAYLOAD,
    login_headers,
    login_user,
    promote_to_admin,
    register_user,
)

ME_URL = "/api/v1/users/me"
USERS_URL = "/api/v1/users"


async def _user_id(client: AsyncClient, headers: dict[str, str], email: str) -> str:
    response = await client.get(USERS_URL, headers=headers)
    assert response.status_code == 200, response.text
    for item in response.json()["items"]:
        if item["email"] == email:
            return str(item["id"])
    raise AssertionError(f"{email} không có trong danh sách")


async def test_get_me_requires_token(client: AsyncClient) -> None:
    response = await client.get(ME_URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert response.headers["www-authenticate"] == "Bearer"


async def test_get_me_rejects_bad_token(client: AsyncClient) -> None:
    response = await client.get(ME_URL, headers={"Authorization": "Bearer nonsense"})

    assert response.status_code == 401


async def test_get_me_rejects_token_with_garbage_subject(client: AsyncClient) -> None:
    import jwt

    from app.core.config import get_settings

    settings = get_settings()
    token = jwt.encode(
        {
            "sub": "khong-phai-uuid",
            "type": "access",
            "jti": "abc",
            "iat": 1,
            "exp": 4102444800,
        },
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = await client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})

    # token ký đúng nhưng sub rác vẫn là 401, không được để 500
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


async def test_change_password_revokes_old_refresh_token(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    tokens = await login_user(client)
    response = await client.patch(
        ME_URL,
        headers=auth_headers,
        json={"current_password": USER_PAYLOAD["password"], "password": "newsecret123"},
    )
    assert response.status_code == 200

    refreshed = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    assert refreshed.status_code == 401


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


async def test_member_cannot_list_users(client: AsyncClient, other_headers: dict[str, str]) -> None:
    response = await client.get(USERS_URL, headers=other_headers)

    assert response.status_code == 403


async def test_member_cannot_update_or_delete_other_user(
    client: AsyncClient, auth_headers: dict[str, str], other_headers: dict[str, str]
) -> None:
    updated = await client.patch(
        USERS_URL + "/me", headers=other_headers, json={"full_name": "Other Name"}
    )
    assert updated.status_code == 200
    target_id = (await client.get(USERS_URL + "/me", headers=other_headers)).json()["id"]

    for response in (
        await client.patch(
            USERS_URL + f"/{target_id}", headers=auth_headers, json={"role": "ADMIN"}
        ),
        await client.delete(USERS_URL + f"/{target_id}", headers=auth_headers),
    ):
        assert response.status_code == 403


async def test_admin_can_list_users(
    client: AsyncClient, admin_headers: dict[str, str], other_user: dict[str, Any]
) -> None:
    response = await client.get(USERS_URL, headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert body["items"][0]["role"] == "ADMIN"


async def test_admin_cannot_delete_self(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    me = await client.get(ME_URL, headers=admin_headers)
    response = await client.delete(USERS_URL + "/" + me.json()["id"], headers=admin_headers)

    assert response.status_code == 400


async def test_admin_cannot_lock_self(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    me = await client.get(ME_URL, headers=admin_headers)
    response = await client.patch(
        USERS_URL + "/" + me.json()["id"], headers=admin_headers, json={"is_active": False}
    )

    assert response.status_code == 400


async def test_admin_cannot_remove_last_admin(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    # chỉ có một admin là chính mình, đổi role sẽ khiến hệ thống không còn admin
    me = await client.get(ME_URL, headers=admin_headers)
    response = await client.patch(
        USERS_URL + "/" + me.json()["id"], headers=admin_headers, json={"role": "MEMBER"}
    )

    assert response.status_code == 400


async def test_admin_can_delete_member_and_token_stops_working(
    client: AsyncClient,
    admin_headers: dict[str, str],
    other_user: dict[str, Any],
) -> None:
    other_headers = await login_headers(client, "other@example.com")
    users = await client.get(USERS_URL, headers=admin_headers)
    target = next(item for item in users.json()["items"] if item["email"] == "other@example.com")

    deleted = await client.delete(USERS_URL + "/" + target["id"], headers=admin_headers)
    assert deleted.status_code == 204

    after = await client.get(ME_URL, headers=other_headers)
    assert after.status_code == 401


async def test_admin_locks_member_and_refresh_token_is_revoked(
    client: AsyncClient,
    admin_headers: dict[str, str],
    other_user: dict[str, Any],
) -> None:
    tokens = await login_user(client, email="other@example.com")
    users = await client.get(USERS_URL, headers=admin_headers)
    target = next(item for item in users.json()["items"] if item["email"] == "other@example.com")

    locked = await client.patch(
        USERS_URL + "/" + target["id"], headers=admin_headers, json={"is_active": False}
    )
    assert locked.status_code == 200

    refreshed = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refreshed.status_code == 401


async def test_admin_can_promote_member(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    admin_headers: dict[str, str],
    other_user: dict[str, Any],
) -> None:
    await promote_to_admin(session_factory, "other@example.com")
    users = await client.get(USERS_URL, headers=admin_headers)
    target = next(item for item in users.json()["items"] if item["email"] == "other@example.com")

    response = await client.patch(
        USERS_URL + "/" + target["id"], headers=admin_headers, json={"full_name": "Other Updated"}
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Other Updated"


async def test_password_longer_than_72_bytes_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register", json={**USER_PAYLOAD, "password": "a" * 73}
    )

    assert response.status_code == 422


async def test_change_password_longer_than_72_bytes_is_rejected(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.patch(
        ME_URL,
        headers=auth_headers,
        json={"current_password": USER_PAYLOAD["password"], "password": "ă" * 40},
    )

    # 40 ký tự nhưng 80 byte, vượt giới hạn bcrypt
    assert response.status_code == 422


async def test_update_me_rejects_null_password(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.patch(ME_URL, headers=auth_headers, json={"password": None})

    assert response.status_code == 422
