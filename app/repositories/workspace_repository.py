"""Repository cho workspace và thành viên workspace."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.repositories.sqlalchemy_repo import SqlAlchemyRepository


class WorkspaceRepository(SqlAlchemyRepository[Workspace]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Workspace, Workspace.created_at, Workspace.id)

    async def create_with_owner(self, name: str, owner_id: UUID) -> Workspace:
        """Tạo workspace và gắn owner trong cùng một transaction."""
        workspace = Workspace(name=name, owner_id=owner_id)
        self._session.add(workspace)
        await self._session.flush()
        self._session.add(
            WorkspaceMember(workspace_id=workspace.id, user_id=owner_id, role=WorkspaceRole.OWNER)
        )
        await self._session.flush()
        await self._session.refresh(workspace)
        return workspace

    async def list_for_user(
        self, user_id: UUID, *, offset: int, limit: int
    ) -> tuple[Sequence[Workspace], int]:
        """Chỉ trả về workspace mà user là thành viên."""
        membership = select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == user_id)
        stmt = select(Workspace).where(Workspace.id.in_(membership))
        return await self._paginate(stmt, offset=offset, limit=limit)

    async def get_member(self, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None:
        result = await self._session.scalars(
            select(WorkspaceMember)
            .options(joinedload(WorkspaceMember.user))
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        return result.first()

    async def list_members(self, workspace_id: UUID) -> Sequence[WorkspaceMember]:
        result = await self._session.scalars(
            select(WorkspaceMember)
            .options(joinedload(WorkspaceMember.user))
            .where(WorkspaceMember.workspace_id == workspace_id)
            .order_by(WorkspaceMember.joined_at)
        )
        return result.all()

    async def add_member(self, member: WorkspaceMember) -> WorkspaceMember:
        self._session.add(member)
        await self._session.flush()
        return member

    async def update_member_role(self, member: WorkspaceMember, role: WorkspaceRole) -> None:
        member.role = role
        await self._session.flush()

    async def remove_member(self, member: WorkspaceMember) -> None:
        await self._session.delete(member)
        await self._session.flush()
