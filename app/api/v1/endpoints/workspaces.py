"""Endpoint CRUD cho workspace và thành viên. Owner mới sửa được workspace."""

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, PaginationDep, WorkspaceServiceDep
from app.api.responses import (
    CONFLICT,
    FORBIDDEN,
    UNAUTHORIZED,
    VALIDATION_ERROR,
    not_found,
)
from app.core.messages import MSG_WORKSPACE_NOT_FOUND
from app.schemas.common import Page
from app.schemas.workspace import (
    MemberInvite,
    MemberRead,
    MemberRoleUpdate,
    WorkspaceCreate,
    WorkspaceRead,
    WorkspaceUpdate,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

_NOT_FOUND = not_found(MSG_WORKSPACE_NOT_FOUND)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a workspace",
    responses={**UNAUTHORIZED, **VALIDATION_ERROR},
)
async def create_workspace(
    payload: WorkspaceCreate, service: WorkspaceServiceDep, user: CurrentUser
) -> WorkspaceRead:
    return WorkspaceRead.model_validate(await service.create(payload, user))


@router.get(
    "",
    summary="List workspaces you belong to",
    responses={**UNAUTHORIZED, **VALIDATION_ERROR},
)
async def list_workspaces(
    service: WorkspaceServiceDep, pagination: PaginationDep, user: CurrentUser
) -> Page[WorkspaceRead]:
    workspaces, total = await service.list(user, pagination)
    return Page[WorkspaceRead].create(
        [WorkspaceRead.model_validate(workspace) for workspace in workspaces],
        total=total,
        page=pagination.page,
        limit=pagination.limit,
    )


@router.get(
    "/{workspace_id}",
    summary="Get a workspace",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND},
)
async def get_workspace(
    workspace_id: UUID, service: WorkspaceServiceDep, user: CurrentUser
) -> WorkspaceRead:
    return WorkspaceRead.model_validate(await service.get(user, workspace_id))


@router.patch(
    "/{workspace_id}",
    summary="Rename a workspace (owner only)",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND, **VALIDATION_ERROR},
)
async def update_workspace(
    workspace_id: UUID, payload: WorkspaceUpdate, service: WorkspaceServiceDep, user: CurrentUser
) -> WorkspaceRead:
    return WorkspaceRead.model_validate(await service.update(user, workspace_id, payload))


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workspace (owner only)",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND},
)
async def delete_workspace(
    workspace_id: UUID, service: WorkspaceServiceDep, user: CurrentUser
) -> None:
    await service.delete(user, workspace_id)


@router.get(
    "/{workspace_id}/members",
    summary="List workspace members",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND},
)
async def list_members(
    workspace_id: UUID, service: WorkspaceServiceDep, user: CurrentUser
) -> list[MemberRead]:
    members = await service.list_members(user, workspace_id)
    return [MemberRead.model_validate(member) for member in members]


@router.post(
    "/{workspace_id}/members",
    status_code=status.HTTP_201_CREATED,
    summary="Add a member to the workspace (owner only)",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND, **CONFLICT, **VALIDATION_ERROR},
)
async def invite_member(
    workspace_id: UUID, payload: MemberInvite, service: WorkspaceServiceDep, user: CurrentUser
) -> MemberRead:
    return MemberRead.model_validate(await service.invite(user, workspace_id, payload))


@router.patch(
    "/{workspace_id}/members/{member_user_id}",
    summary="Change a member role (owner only)",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND, **VALIDATION_ERROR},
)
async def change_member_role(
    workspace_id: UUID,
    member_user_id: UUID,
    payload: MemberRoleUpdate,
    service: WorkspaceServiceDep,
    user: CurrentUser,
) -> MemberRead:
    member = await service.change_role(user, workspace_id, member_user_id, payload)
    return MemberRead.model_validate(member)


@router.delete(
    "/{workspace_id}/members/{member_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from the workspace (owner only)",
    responses={**UNAUTHORIZED, **FORBIDDEN, **_NOT_FOUND},
)
async def remove_member(
    workspace_id: UUID, member_user_id: UUID, service: WorkspaceServiceDep, user: CurrentUser
) -> None:
    await service.remove_member(user, workspace_id, member_user_id)
