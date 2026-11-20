"""Test project: tạo trong workspace, sửa, archive và xoá theo quyền."""

from typing import Any

from httpx import AsyncClient

from tests.conftest import WORKSPACES_URL, create_project, create_workspace, invite_member

PROJECTS_URL = "/api/v1/projects"


async def test_owner_can_create_project(
    client: AsyncClient, auth_headers: dict[str, str], workspace: dict[str, Any]
) -> None:
    project = await create_project(client, auth_headers, workspace["id"], name="Sprint 1")

    assert project["name"] == "Sprint 1"
    assert project["workspace_id"] == workspace["id"]
    assert project["status"] == "ACTIVE"


async def test_create_project_in_missing_workspace_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        f"{WORKSPACES_URL}/00000000-0000-0000-0000-000000000000/projects",
        json={"name": "x"},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Workspace not found"


async def test_viewer_cannot_create_project(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace: dict[str, Any],
    other_headers: dict[str, str],
) -> None:
    await invite_member(client, auth_headers, workspace["id"], "other@example.com", "VIEWER")

    response = await client.post(
        f"{WORKSPACES_URL}/{workspace['id']}/projects",
        json={"name": "nope"},
        headers=other_headers,
    )

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Your workspace role does not allow this action"


async def test_editor_can_create_project(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace: dict[str, Any],
    other_headers: dict[str, str],
) -> None:
    await invite_member(client, auth_headers, workspace["id"], "other@example.com", "EDITOR")

    response = await client.post(
        f"{WORKSPACES_URL}/{workspace['id']}/projects",
        json={"name": "Editor made this"},
        headers=other_headers,
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Editor made this"


async def test_list_projects_in_workspace(
    client: AsyncClient, auth_headers: dict[str, str], workspace: dict[str, Any]
) -> None:
    await create_project(client, auth_headers, workspace["id"], name="One")
    await create_project(client, auth_headers, workspace["id"], name="Two")

    response = await client.get(
        f"{WORKSPACES_URL}/{workspace['id']}/projects", headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [project["name"] for project in body["items"]] == ["One", "Two"]


async def test_list_projects_of_other_workspace_returns_403(
    client: AsyncClient, auth_headers: dict[str, str], other_headers: dict[str, str]
) -> None:
    workspace = await create_workspace(client, other_headers, name="Theirs")

    response = await client.get(
        f"{WORKSPACES_URL}/{workspace['id']}/projects", headers=auth_headers
    )

    assert response.status_code == 403


async def test_get_project(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    response = await client.get(f"{PROJECTS_URL}/{project['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == project["id"]


async def test_get_missing_project_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get(
        f"{PROJECTS_URL}/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Project not found"


async def test_non_member_cannot_get_project(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_headers: dict[str, str],
    workspace: dict[str, Any],
) -> None:
    project = await create_project(client, auth_headers, workspace["id"])

    response = await client.get(f"{PROJECTS_URL}/{project['id']}", headers=other_headers)

    assert response.status_code == 403


async def test_editor_can_update_project(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace: dict[str, Any],
    project: dict[str, Any],
    other_headers: dict[str, str],
) -> None:
    await invite_member(client, auth_headers, workspace["id"], "other@example.com", "EDITOR")

    response = await client.patch(
        f"{PROJECTS_URL}/{project['id']}",
        json={"name": "Renamed", "description": "mô tả mới"},
        headers=other_headers,
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"
    assert response.json()["description"] == "mô tả mới"


async def test_viewer_cannot_update_project(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace: dict[str, Any],
    project: dict[str, Any],
    other_headers: dict[str, str],
) -> None:
    await invite_member(client, auth_headers, workspace["id"], "other@example.com", "VIEWER")

    response = await client.patch(
        f"{PROJECTS_URL}/{project['id']}", json={"name": "Nope"}, headers=other_headers
    )

    assert response.status_code == 403


async def test_update_rejects_null_name(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    response = await client.patch(
        f"{PROJECTS_URL}/{project['id']}", json={"name": None}, headers=auth_headers
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_archive_project(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    response = await client.post(f"{PROJECTS_URL}/{project['id']}/archive", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "ARCHIVED"


async def test_owner_can_delete_project(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    delete_response = await client.delete(f"{PROJECTS_URL}/{project['id']}", headers=auth_headers)
    get_response = await client.get(f"{PROJECTS_URL}/{project['id']}", headers=auth_headers)

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


async def test_editor_cannot_delete_project(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace: dict[str, Any],
    project: dict[str, Any],
    other_headers: dict[str, str],
) -> None:
    await invite_member(client, auth_headers, workspace["id"], "other@example.com", "EDITOR")

    response = await client.delete(f"{PROJECTS_URL}/{project['id']}", headers=other_headers)

    assert response.status_code == 403


async def test_projects_require_auth(client: AsyncClient) -> None:
    response = await client.get(f"{PROJECTS_URL}/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 401
