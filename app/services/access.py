"""Kiểm tra quyền theo workspace và project.

ADMIN của hệ thống đi qua mọi kiểm tra. User thường phải là thành viên workspace
với role tối thiểu tương ứng mới được làm việc trên project hay task bên trong.
"""

from uuid import UUID

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.messages import (
    MSG_INSUFFICIENT_ROLE,
    MSG_NOT_WORKSPACE_MEMBER,
    MSG_PROJECT_ARCHIVED,
    MSG_PROJECT_NOT_FOUND,
    MSG_TASK_NOT_FOUND,
    MSG_WORKSPACE_NOT_FOUND,
)
from app.models.project import Project, ProjectStatus
from app.models.task import TaskModel
from app.models.user import User, UserRole
from app.models.workspace import Workspace, WorkspaceRole
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.workspace_repository import WorkspaceRepository

_ROLE_RANK: dict[WorkspaceRole, int] = {
    WorkspaceRole.VIEWER: 1,
    WorkspaceRole.EDITOR: 2,
    WorkspaceRole.OWNER: 3,
}


async def load_workspace(
    workspaces: WorkspaceRepository,
    workspace_id: UUID,
    user: User,
    minimum: WorkspaceRole,
) -> Workspace:
    """Lấy workspace và kiểm tra user có role tối thiểu trong đó."""
    workspace = await workspaces.get(workspace_id)
    if workspace is None:
        raise NotFoundError(MSG_WORKSPACE_NOT_FOUND, details={"workspace_id": str(workspace_id)})

    if user.role is UserRole.ADMIN:
        return workspace

    member = await workspaces.get_member(workspace_id, user.id)
    if member is None:
        raise ForbiddenError(MSG_NOT_WORKSPACE_MEMBER)
    if _ROLE_RANK[member.role] < _ROLE_RANK[minimum]:
        raise ForbiddenError(MSG_INSUFFICIENT_ROLE)
    return workspace


async def require_workspace(
    workspaces: WorkspaceRepository,
    workspace_id: UUID,
    user: User,
    minimum: WorkspaceRole,
) -> None:
    """Chỉ kiểm tra quyền, không cần dùng lại workspace."""
    await load_workspace(workspaces, workspace_id, user, minimum)


async def require_project(
    projects: ProjectRepository,
    workspaces: WorkspaceRepository,
    project_id: UUID,
    user: User,
    minimum: WorkspaceRole,
    *,
    allow_archived: bool = True,
) -> Project:
    """Lấy project và kiểm tra quyền của user trên workspace chứa nó."""
    project = await projects.get(project_id)
    if project is None:
        raise NotFoundError(MSG_PROJECT_NOT_FOUND, details={"project_id": str(project_id)})
    await require_workspace(workspaces, project.workspace_id, user, minimum)
    if not allow_archived and project.status is ProjectStatus.ARCHIVED:
        raise BadRequestError(MSG_PROJECT_ARCHIVED, details={"project_id": str(project_id)})
    return project


async def load_task_with_project(
    tasks: TaskRepository,
    projects: ProjectRepository,
    workspaces: WorkspaceRepository,
    task_id: UUID,
    user: User,
    minimum: WorkspaceRole,
    *,
    allow_archived: bool = True,
) -> tuple[TaskModel, Project]:
    """Lấy task kèm project đã kiểm tra quyền, tránh truy vấn lặp lại."""
    task = await tasks.get(task_id)
    if task is None:
        raise NotFoundError(MSG_TASK_NOT_FOUND, details={"task_id": str(task_id)})
    project = await require_project(
        projects, workspaces, task.project_id, user, minimum, allow_archived=allow_archived
    )
    return task, project


async def load_task(
    tasks: TaskRepository,
    projects: ProjectRepository,
    workspaces: WorkspaceRepository,
    task_id: UUID,
    user: User,
    minimum: WorkspaceRole,
    *,
    allow_archived: bool = True,
) -> TaskModel:
    """Lấy task và kiểm tra quyền trên project chứa task đó."""
    task, _ = await load_task_with_project(
        tasks, projects, workspaces, task_id, user, minimum, allow_archived=allow_archived
    )
    return task
