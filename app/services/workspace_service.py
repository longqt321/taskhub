"""Nghiệp vụ của workspace và thành viên."""

from collections.abc import Sequence
from uuid import UUID

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.messages import (
    MSG_MEMBER_ALREADY_EXISTS,
    MSG_MEMBER_NOT_FOUND,
    MSG_OWNER_CANNOT_BE_REMOVED,
    MSG_USER_NOT_FOUND,
)
from app.core.pagination import PaginationParams
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.workspace import MemberInvite, MemberRoleUpdate, WorkspaceCreate, WorkspaceUpdate
from app.services.access import load_workspace, require_workspace


class WorkspaceService:
    def __init__(self, workspaces: WorkspaceRepository, users: UserRepository) -> None:
        self._workspaces = workspaces
        self._users = users

    async def create(self, data: WorkspaceCreate, owner: User) -> Workspace:
        return await self._workspaces.create_with_owner(data.name, owner.id)

    async def list(
        self, user: User, pagination: PaginationParams
    ) -> tuple[Sequence[Workspace], int]:
        workspaces, total = await self._workspaces.list_for_user(
            user.id, offset=pagination.offset, limit=pagination.limit
        )
        return workspaces, total

    async def get(self, user: User, workspace_id: UUID) -> Workspace:
        return await load_workspace(self._workspaces, workspace_id, user, WorkspaceRole.VIEWER)

    async def update(self, user: User, workspace_id: UUID, data: WorkspaceUpdate) -> Workspace:
        workspace = await load_workspace(self._workspaces, workspace_id, user, WorkspaceRole.OWNER)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(workspace, field, value)
        return await self._workspaces.update(workspace)

    async def delete(self, user: User, workspace_id: UUID) -> None:
        await require_workspace(self._workspaces, workspace_id, user, WorkspaceRole.OWNER)
        await self._workspaces.delete(workspace_id)

    async def list_members(self, user: User, workspace_id: UUID) -> Sequence[WorkspaceMember]:
        await require_workspace(self._workspaces, workspace_id, user, WorkspaceRole.VIEWER)
        return await self._workspaces.list_members(workspace_id)

    async def invite(self, user: User, workspace_id: UUID, data: MemberInvite) -> WorkspaceMember:
        await require_workspace(self._workspaces, workspace_id, user, WorkspaceRole.OWNER)

        invited = await self._users.get_by_email(data.email)
        if invited is None:
            raise NotFoundError(MSG_USER_NOT_FOUND, details={"email": data.email})
        if await self._workspaces.get_member(workspace_id, invited.id) is not None:
            raise ConflictError(MSG_MEMBER_ALREADY_EXISTS, details={"email": data.email})

        await self._workspaces.add_member(
            WorkspaceMember(workspace_id=workspace_id, user_id=invited.id, role=data.role)
        )
        member = await self._workspaces.get_member(workspace_id, invited.id)
        if member is None:  # pragma: no cover - vừa tạo nên luôn có
            raise NotFoundError(MSG_MEMBER_NOT_FOUND)
        return member

    async def change_role(
        self, user: User, workspace_id: UUID, member_user_id: UUID, data: MemberRoleUpdate
    ) -> WorkspaceMember:
        await require_workspace(self._workspaces, workspace_id, user, WorkspaceRole.OWNER)
        member = await self._get_member(workspace_id, member_user_id)
        if member.role is WorkspaceRole.OWNER:
            raise BadRequestError(MSG_OWNER_CANNOT_BE_REMOVED)
        await self._workspaces.update_member_role(member, data.role)
        return member

    async def remove_member(self, user: User, workspace_id: UUID, member_user_id: UUID) -> None:
        await require_workspace(self._workspaces, workspace_id, user, WorkspaceRole.OWNER)
        member = await self._get_member(workspace_id, member_user_id)
        if member.role is WorkspaceRole.OWNER:
            raise BadRequestError(MSG_OWNER_CANNOT_BE_REMOVED)
        await self._workspaces.remove_member(member)

    async def _get_member(self, workspace_id: UUID, member_user_id: UUID) -> WorkspaceMember:
        member = await self._workspaces.get_member(workspace_id, member_user_id)
        if member is None:
            raise NotFoundError(MSG_MEMBER_NOT_FOUND, details={"user_id": str(member_user_id)})
        return member
