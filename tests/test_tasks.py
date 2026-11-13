"""Test CRUD của resource tasks. Mọi request đều cần đăng nhập."""

from typing import Any, cast

import pytest
from httpx import AsyncClient

from app.services.task_service import TaskService

TASKS_URL = "/api/v1/tasks"


async def _create_task(
    client: AsyncClient, headers: dict[str, str], title: str = "Write tests"
) -> dict[str, Any]:
    response = await client.post(
        TASKS_URL, json={"title": title, "description": "day 1"}, headers=headers
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def test_create_task(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    body = await _create_task(client, auth_headers)

    assert body["title"] == "Write tests"
    assert body["description"] == "day 1"
    assert body["status"] == "TODO"
    assert body["id"]
    assert body["created_at"] <= body["updated_at"]


async def test_create_task_trims_whitespace(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        TASKS_URL, json={"title": "  có khoảng trắng  "}, headers=auth_headers
    )

    assert response.status_code == 201
    assert response.json()["title"] == "có khoảng trắng"


async def test_create_task_rejects_empty_title(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(TASKS_URL, json={"title": ""}, headers=auth_headers)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"][0]["loc"] == ["body", "title"]


async def test_create_task_rejects_whitespace_only_title(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(TASKS_URL, json={"title": "   "}, headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_create_task_rejects_unknown_status(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        TASKS_URL, json={"title": "x", "status": "BLOCKED"}, headers=auth_headers
    )

    assert response.status_code == 422


async def test_get_task(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await _create_task(client, auth_headers)

    response = await client.get(f"{TASKS_URL}/{created['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


async def test_get_missing_task_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get(
        f"{TASKS_URL}/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_list_tasks_is_paginated(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    for index in range(25):
        await _create_task(client, auth_headers, title=f"task-{index:02d}")

    response = await client.get(TASKS_URL, params={"page": 2, "limit": 10}, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 25
    assert body["page"] == 2
    assert body["limit"] == 10
    assert body["pages"] == 3
    assert [task["title"] for task in body["items"]] == [f"task-{i:02d}" for i in range(10, 20)]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"page": 0}])
async def test_list_tasks_rejects_invalid_pagination(
    client: AsyncClient, auth_headers: dict[str, str], params: dict[str, int]
) -> None:
    response = await client.get(TASKS_URL, params=params, headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_update_task_only_changes_provided_fields(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await _create_task(client, auth_headers)

    response = await client.patch(
        f"{TASKS_URL}/{created['id']}", json={"title": "Renamed"}, headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Renamed"
    assert body["description"] == "day 1"
    assert body["status"] == "TODO"
    assert body["created_at"] == created["created_at"]


async def test_update_task_with_empty_body_changes_nothing(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await _create_task(client, auth_headers)

    response = await client.patch(f"{TASKS_URL}/{created['id']}", json={}, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == created["title"]
    assert body["status"] == created["status"]
    assert body["created_at"] == created["created_at"]


async def test_update_task_status(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await _create_task(client, auth_headers)

    response = await client.patch(
        f"{TASKS_URL}/{created['id']}", json={"status": "IN_PROGRESS"}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"


@pytest.mark.parametrize("payload", [{"title": None}, {"status": None}])
async def test_update_task_rejects_null_on_required_fields(
    client: AsyncClient, auth_headers: dict[str, str], payload: dict[str, None]
) -> None:
    created = await _create_task(client, auth_headers)

    response = await client.patch(
        f"{TASKS_URL}/{created['id']}", json=payload, headers=auth_headers
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_update_task_can_clear_description(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    created = await _create_task(client, auth_headers)

    response = await client.patch(
        f"{TASKS_URL}/{created['id']}", json={"description": None}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["description"] is None


async def test_update_missing_task_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.patch(
        f"{TASKS_URL}/00000000-0000-0000-0000-000000000000",
        json={"title": "x"},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_delete_task(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await _create_task(client, auth_headers)

    delete_response = await client.delete(f"{TASKS_URL}/{created['id']}", headers=auth_headers)
    get_response = await client.get(f"{TASKS_URL}/{created['id']}", headers=auth_headers)

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert get_response.status_code == 404


async def test_delete_missing_task_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.delete(
        f"{TASKS_URL}/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_unexpected_error_returns_internal_error_envelope(
    client: AsyncClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    created = await _create_task(client, auth_headers)

    async def boom(self: TaskService, task_id: object) -> object:
        raise RuntimeError("boom")

    monkeypatch.setattr(TaskService, "get", boom)

    response = await client.get(f"{TASKS_URL}/{created['id']}", headers=auth_headers)

    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "internal_error"
    assert error["message"] == "Internal server error"


async def test_tasks_require_auth(client: AsyncClient) -> None:
    response = await client.get(TASKS_URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
