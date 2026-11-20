"""Test workspace: tạo, sửa, xoá và quản lý thành viên."""

from typing import Any

from httpx import AsyncClient

from tests.conftest import WORKSPACES_URL, create_workspace, invite_member

ME_URL = "/api/v1/users/me"


async def test_create_workspace_makes_creator_owner(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    me = await client.get(ME_URL, headers=auth_headers)

    workspace = await create_workspace(client, auth_headers, name="My team")

    assert workspace["name"] == "My team"
    assert workspace["owner_id"] == me.json()["id"]

    members = await client.get(f"{WORKSPACES_URL}/{workspace['id']}/members", headers=auth_headers)
    assert members.status_code == 200
    assert len(members.json()) == 1
    assert members.json()[0]["role"] == "OWNER"
    assert members.json()[0]["user"]["email"] == "intern@example.com"


async def test_list_workspaces_only_returns_mine(
    client: AsyncClient, auth_headers: dict[str, str], other_headers: dict[str, str]
) -> None:
    await create_workspace(client, auth_headers, name="Mine")
    await create_workspace(client, other_headers, name="Not mine")

    response = await client.get(WORKSPACES_URL, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert [workspace["name"] for workspace in body["items"]] == ["Mine"]


async def test_get_missing_workspace_returns_404(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.get(
        f"{WORKSPACES_URL}/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_get_workspace_of_someone_else_returns_403(
    client: AsyncClient, auth_headers: dict[str, str], other_headers: dict[str, str]
) -> None:
    workspace = await create_workspace(client, other_headers, name="Theirs")

    response = await client.get(f"{WORKSPACES_URL}/{workspace['id']}", headers=auth_headers)

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "You are not a member of this workspace"


async def test_owner_can_rename_workspace(
    client: AsyncClient, auth_headers: dict[str, str], workspace: dict[str, Any]
) -> None:
    response = await client.patch(
        f"{WORKSPACES_URL}/{workspace['id']}", json={"name": "Renamed"}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


async def test_rename_rejects_null_name(
    client: AsyncClient, auth_headers: dict[str, str], workspace: dict[str, Any]
) -> None:
    response = await client.patch(
        f"{WORKSPACES_URL}/{workspace['id']}", json={"name": None}, headers=auth_headers
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_owner_can_delete_workspace(
    client: AsyncClient, auth_headers: dict[str, str], workspace: dict[str, Any]
) -> None:
    delete_response = await client.delete(
        f"{WORKSPACES_URL}/{workspace['id']}", headers=auth_headers
    )
    get_response = await client.get(f"{WORKSPACES_URL}/{workspace['id']}", headers=auth_headers)

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


async def test_member_cannot_rename_workspace(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace: dict[str, Any],
    other_headers: dict[str, str],
) -> None:
    await invite_member(client, auth_headers, workspace["id"], "other@example.com", "EDITOR")

    response = await client.patch(
        f"{WORKSPACES_URL}/{workspace['id']}", json={"name": "Nope"}, headers=other_headers
    )

    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Your workspace role does not allow this action"


async def test_owner_can_invite_member(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace: dict[str, Any],
    other_user: dict[str, Any],
) -> None:
    member = await invite_member(
        client, auth_headers, workspace["id"], "other@example.com", "EDITOR"
    )

    assert member["role"] == "EDITOR"
    assert member["user"]["email"] == "other@example.com"


async def test_invite_defaults_to_viewer(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace: dict[str, Any],
    other_user: dict[str, Any],
) -> None:
    response = await client.post(
        f"{WORKSPACES_URL}/{workspace['id']}/members",
        json={"email": "other@example.com"},
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["role"] == "VIEWER"


async def test_invite_unknown_email_returns_404(
    client: AsyncClient, auth_headers: dict[str, str], workspace: dict[str, Any]
) -> None:
    response = await client.post(
        f"{WORKSPACES_URL}/{workspace['id']}/members",
        json={"email": "ghost@example.com"},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "User not found"


async def test_invite_existing_member_returns_409(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace: dict[str, Any],
    other_user: dict[str, Any],
) -> None:
    await invite_member(client, auth_headers, workspace["id"], "other@example.com")

    response = await client.post(
        f"{WORKSPACES_URL}/{workspace['id']}/members",
        json={"email": "other@example.com"},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


async def test_invite_with_owner_role_is_rejected(
    client: AsyncClient, auth_headers: dict[str, str], workspace: dict[str, Any]
) -> None:
    response = await client.post(
        f"{WORKSPACES_URL}/{workspace['id']}/members",
        json={"email": "other@example.com", "role": "OWNER"},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_viewer_cannot_invite(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace: dict[str, Any],
    other_headers: dict[str, str],
) -> None:
    await invite_member(client, auth_headers, workspace["id"], "other@example.com", "VIEWER")

    response = await client.post(
        f"{WORKSPACES_URL}/{workspace['id']}/members",
        json={"email": "intern@example.com"},
        headers=other_headers,
    )

    assert response.status_code == 403


async def test_owner_can_change_member_role(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace: dict[str, Any],
    other_user: dict[str, Any],
) -> None:
    member = await invite_member(client, auth_headers, workspace["id"], "other@example.com")

    response = await client.patch(
        f"{WORKSPACES_URL}/{workspace['id']}/members/{member['user']['id']}",
        json={"role": "EDITOR"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["role"] == "EDITOR"


async def test_change_role_of_owner_is_rejected(
    client: AsyncClient, auth_headers: dict[str, str], workspace: dict[str, Any]
) -> None:
    me = await client.get(ME_URL, headers=auth_headers)

    response = await client.patch(
        f"{WORKSPACES_URL}/{workspace['id']}/members/{me.json()['id']}",
        json={"role": "VIEWER"},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "bad_request"


async def test_change_role_of_missing_member_returns_404(
    client: AsyncClient, auth_headers: dict[str, str], workspace: dict[str, Any]
) -> None:
    response = await client.patch(
        f"{WORKSPACES_URL}/{workspace['id']}/members/00000000-0000-0000-0000-000000000000",
        json={"role": "EDITOR"},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Member not found"


async def test_owner_can_remove_member(
    client: AsyncClient,
    auth_headers: dict[str, str],
    workspace: dict[str, Any],
    other_user: dict[str, Any],
) -> None:
    member = await invite_member(client, auth_headers, workspace["id"], "other@example.com")

    response = await client.delete(
        f"{WORKSPACES_URL}/{workspace['id']}/members/{member['user']['id']}", headers=auth_headers
    )

    assert response.status_code == 204
    members = await client.get(f"{WORKSPACES_URL}/{workspace['id']}/members", headers=auth_headers)
    assert [item["user"]["email"] for item in members.json()] == ["intern@example.com"]


async def test_remove_owner_is_rejected(
    client: AsyncClient, auth_headers: dict[str, str], workspace: dict[str, Any]
) -> None:
    me = await client.get(ME_URL, headers=auth_headers)

    response = await client.delete(
        f"{WORKSPACES_URL}/{workspace['id']}/members/{me.json()['id']}", headers=auth_headers
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "bad_request"


async def test_workspaces_require_auth(client: AsyncClient) -> None:
    response = await client.get(WORKSPACES_URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
