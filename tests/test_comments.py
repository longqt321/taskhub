"""Test comment trên task."""

from typing import Any, cast

from httpx import AsyncClient

from tests.conftest import invite_member

TASKS_URL = "/api/v1/tasks"


async def _create_task(
    client: AsyncClient, headers: dict[str, str], project_id: str
) -> dict[str, Any]:
    response = await client.post(
        TASKS_URL, json={"project_id": project_id, "title": "Task"}, headers=headers
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def _add_comment(
    client: AsyncClient, headers: dict[str, str], task_id: str, content: str = "xong rồi"
) -> dict[str, Any]:
    response = await client.post(
        f"{TASKS_URL}/{task_id}/comments", json={"content": content}, headers=headers
    )
    assert response.status_code == 201, response.text
    return cast("dict[str, Any]", response.json())


async def test_add_comment_returns_author(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    task = await _create_task(client, auth_headers, project["id"])

    body = await _add_comment(client, auth_headers, task["id"])

    assert body["content"] == "xong rồi"
    assert body["task_id"] == task["id"]
    assert body["author"]["full_name"] == "Intern"


async def test_add_comment_rejects_blank_content(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    task = await _create_task(client, auth_headers, project["id"])

    response = await client.post(
        f"{TASKS_URL}/{task['id']}/comments", json={"content": "   "}, headers=auth_headers
    )

    assert response.status_code == 422


async def test_list_comments_in_order(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    task = await _create_task(client, auth_headers, project["id"])
    await _add_comment(client, auth_headers, task["id"], "một")
    await _add_comment(client, auth_headers, task["id"], "hai")

    response = await client.get(f"{TASKS_URL}/{task['id']}/comments", headers=auth_headers)

    assert response.status_code == 200
    assert [item["content"] for item in response.json()] == ["một", "hai"]


async def test_author_can_delete_own_comment(
    client: AsyncClient, auth_headers: dict[str, str], project: dict[str, Any]
) -> None:
    task = await _create_task(client, auth_headers, project["id"])
    comment = await _add_comment(client, auth_headers, task["id"])

    response = await client.delete(
        f"{TASKS_URL}/{task['id']}/comments/{comment['id']}", headers=auth_headers
    )
    listing = await client.get(f"{TASKS_URL}/{task['id']}/comments", headers=auth_headers)

    assert response.status_code == 204
    assert listing.json() == []


async def test_other_member_cannot_delete_someone_elses_comment(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_headers: dict[str, str],
    other_user: dict[str, Any],
    workspace: dict[str, Any],
    project: dict[str, Any],
) -> None:
    await invite_member(client, auth_headers, workspace["id"], other_user["email"], "EDITOR")
    task = await _create_task(client, auth_headers, project["id"])
    comment = await _add_comment(client, auth_headers, task["id"])

    response = await client.delete(
        f"{TASKS_URL}/{task['id']}/comments/{comment['id']}", headers=other_headers
    )

    assert response.status_code == 403


async def test_workspace_owner_can_delete_any_comment(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_headers: dict[str, str],
    other_user: dict[str, Any],
    workspace: dict[str, Any],
    project: dict[str, Any],
) -> None:
    await invite_member(client, auth_headers, workspace["id"], other_user["email"], "EDITOR")
    task = await _create_task(client, other_headers, project["id"])
    comment = await _add_comment(client, other_headers, task["id"])

    response = await client.delete(
        f"{TASKS_URL}/{task['id']}/comments/{comment['id']}", headers=auth_headers
    )

    assert response.status_code == 204


async def test_non_member_cannot_read_comments(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_headers: dict[str, str],
    other_user: dict[str, Any],
    project: dict[str, Any],
) -> None:
    task = await _create_task(client, auth_headers, project["id"])

    response = await client.get(f"{TASKS_URL}/{task['id']}/comments", headers=other_headers)

    assert response.status_code == 403


async def test_comment_on_missing_task(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.get(
        f"{TASKS_URL}/00000000-0000-0000-0000-000000000000/comments", headers=auth_headers
    )

    assert response.status_code == 404
