"""CRUD and error-path tests for the items resource."""

from typing import Any, cast

from httpx import AsyncClient

ITEMS_URL = "/api/v1/items"


async def _create_item(client: AsyncClient, name: str = "Write tests") -> dict[str, Any]:
    response = await client.post(ITEMS_URL, json={"name": name, "description": "day 1"})
    assert response.status_code == 201
    return cast("dict[str, Any]", response.json())


async def test_create_item(client: AsyncClient) -> None:
    body = await _create_item(client)

    assert body["name"] == "Write tests"
    assert body["description"] == "day 1"
    assert body["id"]
    assert body["created_at"] == body["updated_at"]


async def test_create_item_rejects_empty_name(client: AsyncClient) -> None:
    response = await client.post(ITEMS_URL, json={"name": ""})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"][0]["loc"] == ["body", "name"]


async def test_get_item(client: AsyncClient) -> None:
    created = await _create_item(client)

    response = await client.get(f"{ITEMS_URL}/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


async def test_get_missing_item_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"{ITEMS_URL}/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_list_items_is_paginated(client: AsyncClient) -> None:
    for index in range(25):
        await _create_item(client, name=f"item-{index:02d}")

    response = await client.get(ITEMS_URL, params={"page": 2, "limit": 10})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 25
    assert body["page"] == 2
    assert body["limit"] == 10
    assert body["pages"] == 3
    assert [item["name"] for item in body["items"]] == [f"item-{i:02d}" for i in range(10, 20)]


async def test_list_items_rejects_invalid_limit(client: AsyncClient) -> None:
    response = await client.get(ITEMS_URL, params={"limit": 0})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_update_item_only_changes_provided_fields(client: AsyncClient) -> None:
    created = await _create_item(client)

    response = await client.patch(f"{ITEMS_URL}/{created['id']}", json={"name": "Renamed"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renamed"
    assert body["description"] == "day 1"
    assert body["created_at"] == created["created_at"]
    assert body["updated_at"] > created["updated_at"]


async def test_update_missing_item_returns_404(client: AsyncClient) -> None:
    response = await client.patch(
        f"{ITEMS_URL}/00000000-0000-0000-0000-000000000000", json={"name": "x"}
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_delete_item(client: AsyncClient) -> None:
    created = await _create_item(client)

    delete_response = await client.delete(f"{ITEMS_URL}/{created['id']}")
    get_response = await client.get(f"{ITEMS_URL}/{created['id']}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert get_response.status_code == 404


async def test_delete_missing_item_returns_404(client: AsyncClient) -> None:
    response = await client.delete(f"{ITEMS_URL}/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
