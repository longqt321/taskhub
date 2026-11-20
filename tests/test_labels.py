"""Test label trong project và gán/bỏ label cho task."""

from typing import Any, cast

from httpx import AsyncClient

from tests.conftest import create_project, invite_member

LABELS_URL = "/api/v1/labels"
TASKS_URL = "/api/v1/tasks"


async def _create_label(
    client: AsyncClient,
    headers: dict[str, str],
    project_id: str,
    name: str = "bug",
    color: str = "#FF0000",
) -> dict[str, Any]:
    response = await client.post(
        f"/api/v1/projects/{project_id}/labels",
        json={"name": name, "color": color},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def _create_task(
    client: AsyncClient, headers: dict[str, str], project_id: str, **extra: Any
) -> dict[str, Any]:
    response = await client.post(
        TASKS_URL,
        json={"project_id": project_id, "title": "Task", **extra},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def test_create_label(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    body = await _create_label(client, auth_headers, project["id"])

    assert body["name"] == "bug"
    assert body["color"] == "#FF0000"
    assert body["project_id"] == project["id"]


async def test_create_label_rejects_duplicate_name(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    await _create_label(client, auth_headers, project["id"])

    response = await client.post(
        f"/api/v1/projects/{project['id']}/labels",
        json={"name": "bug"},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


async def test_create_label_rejects_bad_color(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    response = await client.post(
        f"/api/v1/projects/{project['id']}/labels",
        json={"name": "bug", "color": "red"},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_list_labels_of_project(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    await _create_label(client, auth_headers, project["id"], name="bug")
    await _create_label(client, auth_headers, project["id"], name="docs", color="#00FF00")

    response = await client.get(f"/api/v1/projects/{project['id']}/labels", headers=auth_headers)

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["bug", "docs"]


async def test_viewer_cannot_create_label(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_headers: dict[str, str],
    other_user: dict[str, Any],
    workspace: dict[str, Any],
    project: dict[str, Any],
) -> None:
    await invite_member(client, auth_headers, workspace["id"], other_user["email"], "VIEWER")

    response = await client.post(
        f"/api/v1/projects/{project['id']}/labels",
        json={"name": "bug"},
        headers=other_headers,
    )

    assert response.status_code == 403


async def test_non_member_cannot_list_labels(
    client: AsyncClient,
    other_headers: dict[str, str],
    other_user: dict[str, Any],
    project: dict[str, Any],
) -> None:
    response = await client.get(f"/api/v1/projects/{project['id']}/labels", headers=other_headers)

    assert response.status_code == 403


async def test_update_label(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    label = await _create_label(client, auth_headers, project["id"])

    response = await client.patch(
        f"{LABELS_URL}/{label['id']}",
        json={"name": "defect", "color": "#123456"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["name"] == "defect"
    assert response.json()["color"] == "#123456"


async def test_update_label_rejects_null_name(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    label = await _create_label(client, auth_headers, project["id"])

    response = await client.patch(
        f"{LABELS_URL}/{label['id']}", json={"name": None}, headers=auth_headers
    )

    assert response.status_code == 422


async def test_delete_label(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    label = await _create_label(client, auth_headers, project["id"])

    deleted = await client.delete(f"{LABELS_URL}/{label['id']}", headers=auth_headers)
    listing = await client.get(f"/api/v1/projects/{project['id']}/labels", headers=auth_headers)

    assert deleted.status_code == 204
    assert listing.json() == []


async def test_attach_label_to_task(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    label = await _create_label(client, auth_headers, project["id"])
    task = await _create_task(client, auth_headers, project["id"])

    response = await client.put(
        f"{TASKS_URL}/{task['id']}/labels/{label['id']}", headers=auth_headers
    )
    detail = await client.get(f"{TASKS_URL}/{task['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["bug"]
    assert [item["name"] for item in detail.json()["labels"]] == ["bug"]


async def test_attach_label_twice_is_idempotent(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    label = await _create_label(client, auth_headers, project["id"])
    task = await _create_task(client, auth_headers, project["id"])
    url = f"{TASKS_URL}/{task['id']}/labels/{label['id']}"
    await client.put(url, headers=auth_headers)

    response = await client.put(url, headers=auth_headers)

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["bug"]


async def test_attach_label_from_other_project_is_rejected(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace: dict[str, Any],
    project: dict[str, Any],
) -> None:
    other_project = await create_project(client, auth_headers, workspace["id"], name="Other")
    label = await _create_label(client, auth_headers, other_project["id"])
    task = await _create_task(client, auth_headers, project["id"])

    response = await client.put(
        f"{TASKS_URL}/{task['id']}/labels/{label['id']}", headers=auth_headers
    )

    assert response.status_code == 400


async def test_detach_label(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    label = await _create_label(client, auth_headers, project["id"])
    task = await _create_task(client, auth_headers, project["id"])
    url = f"{TASKS_URL}/{task['id']}/labels/{label['id']}"
    await client.put(url, headers=auth_headers)

    response = await client.delete(url, headers=auth_headers)
    detail = await client.get(f"{TASKS_URL}/{task['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []
    assert detail.json()["labels"] == []


async def test_detach_label_not_attached(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    label = await _create_label(client, auth_headers, project["id"])
    task = await _create_task(client, auth_headers, project["id"])

    response = await client.delete(
        f"{TASKS_URL}/{task['id']}/labels/{label['id']}", headers=auth_headers
    )

    assert response.status_code == 404
