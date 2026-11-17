"""Test CRUD của resource tasks. Mọi request đều cần đăng nhập."""

from typing import Any, cast

import pytest
from httpx import AsyncClient

from app.services.task_service import TaskService
from tests.conftest import (
    create_project,
    create_workspace,
    invite_member,
    login_headers,
    register_user,
)

TASKS_URL = "/api/v1/tasks"


async def _create_task(
    client: AsyncClient,
    headers: dict[str, str],
    project_id: str,
    title: str = "Write tests",
    **extra: Any,
) -> dict[str, Any]:
    response = await client.post(
        TASKS_URL,
        json={"project_id": project_id, "title": title, "description": "day 4", **extra},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def test_create_task(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    body = await _create_task(client, auth_headers, project["id"])

    assert body["title"] == "Write tests"
    assert body["description"] == "day 4"
    assert body["status"] == "TODO"
    assert body["priority"] == "MEDIUM"
    assert body["project_id"] == project["id"]
    assert body["assignee_id"] is None
    assert body["due_date"] is None
    assert body["created_at"] <= body["updated_at"]


async def test_create_task_sets_created_by(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    me = await client.get("/api/v1/users/me", headers=auth_headers)

    body = await _create_task(client, auth_headers, project["id"])

    assert body["created_by"] == me.json()["id"]


async def test_create_task_trims_title(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    body = await _create_task(client, auth_headers, project["id"], title="  có khoảng trắng  ")

    assert body["title"] == "có khoảng trắng"


@pytest.mark.parametrize("title", ["", "   "])
async def test_create_task_rejects_blank_title(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project: dict[str, Any],
    title: str,
) -> None:
    response = await client.post(
        TASKS_URL, json={"project_id": project["id"], "title": title}, headers=auth_headers
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_create_task_requires_project(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(TASKS_URL, json={"title": "No project"}, headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["loc"] == ["body", "project_id"]


async def test_create_task_in_missing_project_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        TASKS_URL,
        json={"project_id": "00000000-0000-0000-0000-000000000000", "title": "x"},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_create_task_with_unknown_assignee_returns_404(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    response = await client.post(
        TASKS_URL,
        json={
            "project_id": project["id"],
            "title": "x",
            "assignee_id": "00000000-0000-0000-0000-000000000000",
        },
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Assignee not found"


async def test_create_task_with_assignee(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project: dict[str, Any],
    other_headers: dict[str, str],
) -> None:
    other = await client.get("/api/v1/users/me", headers=other_headers)

    body = await _create_task(client, auth_headers, project["id"], assignee_id=other.json()["id"])

    assert body["assignee_id"] == other.json()["id"]


async def test_create_task_rejects_unknown_status(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    response = await client.post(
        TASKS_URL,
        json={"project_id": project["id"], "title": "x", "status": "BLOCKED"},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_get_task(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    created = await _create_task(client, auth_headers, project["id"])

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


async def test_list_tasks_can_filter_by_project(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    for index in range(3):
        await _create_task(client, auth_headers, project["id"], title=f"task-{index}")

    response = await client.get(
        TASKS_URL, params={"project_id": project["id"]}, headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert {task["project_id"] for task in body["items"]} == {project["id"]}


async def test_list_tasks_is_paginated(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    for index in range(25):
        await _create_task(client, auth_headers, project["id"], title=f"task-{index:02d}")

    response = await client.get(
        TASKS_URL,
        params={"project_id": project["id"], "page": 2, "limit": 10},
        headers=auth_headers,
    )

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


async def test_list_tasks_only_returns_tasks_from_my_workspaces(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    # Workspace thứ hai của người khác, task trong đó không được lọt vào danh sách của mình.
    await register_user(client, email="third@example.com", full_name="Third")
    third_headers = await login_headers(client, "third@example.com")
    third_workspace = await create_workspace(client, third_headers, name="Elsewhere")
    third_project = await create_project(
        client, third_headers, third_workspace["id"], name="Theirs"
    )
    await _create_task(client, third_headers, third_project["id"], title="not mine")

    await _create_task(client, auth_headers, project["id"], title="mine")

    response = await client.get(TASKS_URL, headers=auth_headers)

    assert response.status_code == 200
    assert [task["title"] for task in response.json()["items"]] == ["mine"]


async def test_update_task_only_changes_provided_fields(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    created = await _create_task(client, auth_headers, project["id"])

    response = await client.patch(
        f"{TASKS_URL}/{created['id']}", json={"title": "Renamed"}, headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Renamed"
    assert body["description"] == "day 4"
    assert body["status"] == "TODO"
    assert body["created_at"] == created["created_at"]


async def test_update_task_with_empty_body_changes_nothing(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    created = await _create_task(client, auth_headers, project["id"])

    response = await client.patch(f"{TASKS_URL}/{created['id']}", json={}, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == created["title"]
    assert body["status"] == created["status"]
    assert body["priority"] == created["priority"]


async def test_update_task_status_and_priority(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    created = await _create_task(client, auth_headers, project["id"])

    response = await client.patch(
        f"{TASKS_URL}/{created['id']}",
        json={"status": "IN_PROGRESS", "priority": "URGENT"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"
    assert response.json()["priority"] == "URGENT"


async def test_update_task_due_date_and_assignee(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project: dict[str, Any],
    other_headers: dict[str, str],
) -> None:
    created = await _create_task(client, auth_headers, project["id"])
    other = await client.get("/api/v1/users/me", headers=other_headers)

    response = await client.patch(
        f"{TASKS_URL}/{created['id']}",
        json={"assignee_id": other.json()["id"], "due_date": "2026-12-01T09:00:00Z"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["assignee_id"] == other.json()["id"]
    assert response.json()["due_date"].startswith("2026-12-01T09:00:00")


@pytest.mark.parametrize("payload", [{"title": None}, {"status": None}, {"priority": None}])
async def test_update_task_rejects_null_on_required_fields(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project: dict[str, Any],
    payload: dict[str, None],
) -> None:
    created = await _create_task(client, auth_headers, project["id"])

    response = await client.patch(
        f"{TASKS_URL}/{created['id']}", json=payload, headers=auth_headers
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_update_task_can_clear_optional_fields(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project: dict[str, Any],
    other_headers: dict[str, str],
) -> None:
    other = await client.get("/api/v1/users/me", headers=other_headers)
    created = await _create_task(
        client, auth_headers, project["id"], assignee_id=other.json()["id"]
    )

    response = await client.patch(
        f"{TASKS_URL}/{created['id']}",
        json={"description": None, "assignee_id": None, "due_date": None},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["description"] is None
    assert body["assignee_id"] is None
    assert body["due_date"] is None


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


async def test_delete_task(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    created = await _create_task(client, auth_headers, project["id"])

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


async def test_tasks_require_auth(client: AsyncClient) -> None:
    response = await client.get(TASKS_URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


async def test_viewer_cannot_create_task(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace: dict[str, Any],
    project: dict[str, Any],
    other_headers: dict[str, str],
) -> None:
    await invite_member(client, auth_headers, workspace["id"], "other@example.com", "VIEWER")

    response = await client.post(
        TASKS_URL,
        json={"project_id": project["id"], "title": "nope"},
        headers=other_headers,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


async def test_non_member_cannot_read_task(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project: dict[str, Any],
    other_headers: dict[str, str],
) -> None:
    created = await _create_task(client, auth_headers, project["id"])

    response = await client.get(f"{TASKS_URL}/{created['id']}", headers=other_headers)

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "You are not a member of this workspace"


async def test_editor_can_update_task(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace: dict[str, Any],
    project: dict[str, Any],
    other_headers: dict[str, str],
) -> None:
    await invite_member(client, auth_headers, workspace["id"], "other@example.com", "EDITOR")
    created = await _create_task(client, auth_headers, project["id"])

    response = await client.patch(
        f"{TASKS_URL}/{created['id']}", json={"status": "DONE"}, headers=other_headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "DONE"


async def test_unexpected_error_returns_internal_error_envelope(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created = await _create_task(client, auth_headers, project["id"])

    async def boom(self: TaskService, *args: object, **kwargs: object) -> object:
        raise RuntimeError("boom")

    monkeypatch.setattr(TaskService, "get", boom)

    response = await client.get(f"{TASKS_URL}/{created['id']}", headers=auth_headers)

    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "internal_error"
    assert error["message"] == "Internal server error"
