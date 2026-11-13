"""Test đăng ký, đăng nhập, refresh, logout."""

from httpx import AsyncClient

from tests.conftest import USER_PAYLOAD, login_user, register_user

AUTH_URL = "/api/v1/auth"


async def test_register_returns_profile_without_password(client: AsyncClient) -> None:
    response = await client.post(AUTH_URL + "/register", json=USER_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == USER_PAYLOAD["email"]
    assert body["role"] == "MEMBER"
    assert body["is_active"] is True
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_rejects_duplicate_email(client: AsyncClient) -> None:
    await register_user(client)

    response = await client.post(AUTH_URL + "/register", json=USER_PAYLOAD)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


async def test_register_rejects_short_password(client: AsyncClient) -> None:
    response = await client.post(AUTH_URL + "/register", json={**USER_PAYLOAD, "password": "short"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_register_rejects_invalid_email(client: AsyncClient) -> None:
    response = await client.post(
        AUTH_URL + "/register", json={**USER_PAYLOAD, "email": "not-an-email"}
    )

    assert response.status_code == 422


async def test_login_returns_token_pair(client: AsyncClient) -> None:
    await register_user(client)

    tokens = await login_user(client)

    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"]
    assert tokens["refresh_token"]


async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    await register_user(client)

    response = await client.post(
        AUTH_URL + "/login",
        json={"email": USER_PAYLOAD["email"], "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


async def test_login_rejects_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        AUTH_URL + "/login",
        json={"email": "nobody@example.com", "password": "secret12345"},
    )

    assert response.status_code == 401


async def test_refresh_returns_new_pair_and_rotates(client: AsyncClient) -> None:
    await register_user(client)
    tokens = await login_user(client)

    response = await client.post(
        AUTH_URL + "/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    # token cũ đã bị thu hồi, dùng lại phải bị từ chối
    reuse = await client.post(
        AUTH_URL + "/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert reuse.status_code == 401


async def test_refresh_rejects_garbage_token(client: AsyncClient) -> None:
    response = await client.post(AUTH_URL + "/refresh", json={"refresh_token": "abc.def.ghi"})

    assert response.status_code == 401


async def test_refresh_rejects_access_token(client: AsyncClient) -> None:
    await register_user(client)
    tokens = await login_user(client)

    response = await client.post(
        AUTH_URL + "/refresh", json={"refresh_token": tokens["access_token"]}
    )

    assert response.status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient) -> None:
    await register_user(client)
    tokens = await login_user(client)

    logout = await client.post(
        AUTH_URL + "/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert logout.status_code == 200

    after = await client.post(
        AUTH_URL + "/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert after.status_code == 401
