"""Test Redis cache theo project và background task gửi mail khi assign task."""

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from redis.asyncio import Redis

from app.main import app
from tests.conftest import invite_member


@pytest.fixture
async def redis_client() -> AsyncIterator[Redis]:
    client = Redis.from_url("redis://localhost:6379/15", decode_responses=True)
    await client.flushdb()
    app.state.redis = client
    try:
        yield client
    finally:
        await client.flushdb()
        app.state.redis = None
        await client.aclose()


async def test_project_tasks_cached_and_invalidated_on_create(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project: dict[str, Any],
    redis_client: Redis,
) -> None:
    url = f"/api/v1/tasks?project_id={project['id']}"

    first = await client.get(url, headers=auth_headers)
    assert first.status_code == 200
    assert first.json()["total"] == 0
    keys = [key async for key in redis_client.scan_iter(match=f"tasks:project:{project['id']}:*")]
    assert len(keys) == 1

    # tạo task mới phải xoá cache của project, lần GET sau thấy task mới
    created = await client.post(
        "/api/v1/tasks",
        json={"project_id": project["id"], "title": "Cached task"},
        headers=auth_headers,
    )
    assert created.status_code == 201
    keys_after = [
        key async for key in redis_client.scan_iter(match=f"tasks:project:{project['id']}:*")
    ]
    assert keys_after == []

    second = await client.get(url, headers=auth_headers)
    assert second.status_code == 200
    assert second.json()["total"] == 1


async def test_cache_invalidated_when_label_attached(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project: dict[str, Any],
    redis_client: Redis,
) -> None:
    task = (
        await client.post(
            "/api/v1/tasks",
            json={"project_id": project["id"], "title": "T"},
            headers=auth_headers,
        )
    ).json()
    label = (
        await client.post(
            f"/api/v1/projects/{project['id']}/labels",
            json={"name": "urgent"},
            headers=auth_headers,
        )
    ).json()

    url = f"/api/v1/tasks?project_id={project['id']}"
    await client.get(url, headers=auth_headers)

    await client.put(f"/api/v1/tasks/{task['id']}/labels/{label['id']}", headers=auth_headers)

    refreshed = await client.get(url, headers=auth_headers)
    assert [item["name"] for item in refreshed.json()["items"][0]["labels"]] == ["urgent"]


async def test_assign_task_triggers_background_email(
    client: AsyncClient,
    auth_headers: dict[str, str],
    other_headers: dict[str, str],
    other_user: dict[str, Any],
    workspace: dict[str, Any],
    project: dict[str, Any],
) -> None:
    await invite_member(client, auth_headers, workspace["id"], other_user["email"], "EDITOR")
    other_id = (await client.get("/api/v1/users/me", headers=other_headers)).json()["id"]

    with patch("app.api.v1.endpoints.tasks.send_task_assigned_email") as mock_send:
        created = await client.post(
            "/api/v1/tasks",
            json={"project_id": project["id"], "title": "Fix bug", "assignee_id": other_id},
            headers=auth_headers,
        )
        assert created.status_code == 201
        mock_send.assert_called_once()
        assert mock_send.call_args.args[0] == other_user["email"]
        assert mock_send.call_args.args[1] == "Fix bug"

        mock_send.reset_mock()
        # sửa title nhưng không đổi assignee thì không gửi lại
        task_id = created.json()["id"]
        await client.patch(
            f"/api/v1/tasks/{task_id}", json={"title": "Fix bug v2"}, headers=auth_headers
        )
        mock_send.assert_not_called()
