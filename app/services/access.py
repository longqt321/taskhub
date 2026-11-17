"""Kiểm tra quyền theo workspace và project.

ADMIN của hệ thống đi qua mọi kiểm tra. User thường phải là thành viên workspace
với role tối thiểu tương ứng mới được làm việc trên project hay task bên trong.
"""

from uuid import UUID

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.messages import (
    MSG_INSUFFICIENT_ROLE,
    MSG_NOT_WORKSPACE_MEMBER,
    MSG_PROJECT_NOT_FOUND,
    MSG_WORKSPACE_NOT_FOUND,
)
from app.models.project import Project
from app.models.user import User, UserRole
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.repositories.project_repository import ProjectRepository
from app.repositories.workspace_repository import WorkspaceRepository

_ROLE_RANK: dict[WorkspaceRole, int] = {
    WorkspaceRole.VIEWER: 1,
    WorkspaceRole.EDITOR: 2,
    WorkspaceRole.OWNER: 3,
}


async def require_workspace(
    workspaces: WorkspaceRepository,
    workspace_id: UUID,
    user: User,
    minimum: WorkspaceRole,
) -> WorkspaceMember | None:
    """Kiểm tra user có role tối thiểu trong workspace.

    Trả về membership, hoặc None nếu là ADMIN hệ thống.
    """
    workspace = await workspaces.get(workspace_id)
    if workspace is None:
        raise NotFoundError(MSG_WORKSPACE_NOT_FOUND, details={"workspace_id": str(workspace_id)})

    if user.role is UserRole.ADMIN:
        return None

    member = await workspaces.get_member(workspace_id, user.id)
    if member is None:
        raise ForbiddenError(MSG_NOT_WORKSPACE_MEMBER)
    if _ROLE_RANK[member.role] < _ROLE_RANK[minimum]:
        raise ForbiddenError(MSG_INSUFFICIENT_ROLE)
    return member


async def require_project(
    projects: ProjectRepository,
    workspaces: WorkspaceRepository,
    project_id: UUID,
    user: User,
    minimum: WorkspaceRole,
) -> Project:
    """Lấy project và kiểm tra quyền của user trên workspace chứa nó."""
    project = await projects.get(project_id)
    if project is None:
        raise NotFoundError(MSG_PROJECT_NOT_FOUND, details={"project_id": str(project_id)})
    await require_workspace(workspaces, project.workspace_id, user, minimum)
    return project
