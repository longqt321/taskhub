"""Test CRUD của resource items. Mọi request đều cần đăng nhập."""

from typing import Any, cast

from httpx import AsyncClient

ITEMS_URL = "/api/v1/items"


async def _create_item(
    client: AsyncClient, headers: dict[str, str], name: str = "Write tests"
) -> dict[str, Any]:
    response = await client.post(
        ITEMS_URL, json={"name": name, "description": "day 1"}, headers=headers
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def test_items_require_auth(client: AsyncClient) -> None:
    response = await client.get(ITEMS_URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


async def test_create_item(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    body = await _create_item(client, auth_headers)

    assert body["name"] == "Write tests"
    assert body["description"] == "day 1"
    assert body["id"]
    assert body["created_at"] <= body["updated_at"]


async def test_create_item_rejects_empty_name(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(ITEMS_URL, json={"name": ""}, headers=auth_headers)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"][0]["loc"] == ["body", "name"]


async def test_get_item(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await _create_item(client, auth_headers)

    response = await client.get(f"{ITEMS_URL}/{created['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


async def test_get_missing_item_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get(
        f"{ITEMS_URL}/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_list_items_is_paginated(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    for index in range(25):
        await _create_item(client, auth_headers, name=f"item-{index:02d}")

    response = await client.get(ITEMS_URL, params={"page": 2, "limit": 10}, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 25
    assert body["page"] == 2
    assert body["limit"] == 10
    assert body["pages"] == 3
    assert [item["name"] for item in body["items"]] == [f"item-{i:02d}" for i in range(10, 20)]


async def test_list_items_rejects_invalid_limit(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get(ITEMS_URL, params={"limit": 0}, headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_update_item_only_changes_provided_fields(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await _create_item(client, auth_headers)

    response = await client.patch(
        f"{ITEMS_URL}/{created['id']}", json={"name": "Renamed"}, headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renamed"
    assert body["description"] == "day 1"
    assert body["created_at"] == created["created_at"]
    assert body["updated_at"] > created["updated_at"]


async def test_update_item_rejects_null_name(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await _create_item(client, auth_headers)

    response = await client.patch(
        f"{ITEMS_URL}/{created['id']}", json={"name": None}, headers=auth_headers
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_update_item_can_clear_description(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await _create_item(client, auth_headers)

    response = await client.patch(
        f"{ITEMS_URL}/{created['id']}", json={"description": None}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["description"] is None


async def test_update_missing_item_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.patch(
        f"{ITEMS_URL}/00000000-0000-0000-0000-000000000000",
        json={"name": "x"},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_delete_item(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await _create_item(client, auth_headers)

    delete_response = await client.delete(f"{ITEMS_URL}/{created['id']}", headers=auth_headers)
    get_response = await client.get(f"{ITEMS_URL}/{created['id']}", headers=auth_headers)

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert get_response.status_code == 404


async def test_delete_missing_item_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.delete(
        f"{ITEMS_URL}/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
