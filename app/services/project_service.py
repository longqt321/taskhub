"""Nghiệp vụ của project."""

from collections.abc import Sequence
from uuid import UUID

from app.core.pagination import PaginationParams
from app.models.project import Project, ProjectStatus
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.repositories.project_repository import ProjectRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.access import require_project, require_workspace


class ProjectService:
    def __init__(self, projects: ProjectRepository, workspaces: WorkspaceRepository) -> None:
        self._projects = projects
        self._workspaces = workspaces

    async def create(self, user: User, workspace_id: UUID, data: ProjectCreate) -> Project:
        await require_workspace(self._workspaces, workspace_id, user, WorkspaceRole.EDITOR)
        project = Project(workspace_id=workspace_id, name=data.name, description=data.description)
        return await self._projects.add(project)

    async def list(
        self, user: User, workspace_id: UUID, pagination: PaginationParams
    ) -> tuple[Sequence[Project], int]:
        await require_workspace(self._workspaces, workspace_id, user, WorkspaceRole.VIEWER)
        projects, total = await self._projects.list_in_workspace(
            workspace_id, offset=pagination.offset, limit=pagination.limit
        )
        return projects, total

    async def get(self, user: User, project_id: UUID) -> Project:
        return await require_project(
            self._projects, self._workspaces, project_id, user, WorkspaceRole.VIEWER
        )

    async def update(self, user: User, project_id: UUID, data: ProjectUpdate) -> Project:
        project = await require_project(
            self._projects, self._workspaces, project_id, user, WorkspaceRole.EDITOR
        )
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        return await self._projects.update(project)

    async def archive(self, user: User, project_id: UUID) -> Project:
        project = await require_project(
            self._projects, self._workspaces, project_id, user, WorkspaceRole.EDITOR
        )
        project.status = ProjectStatus.ARCHIVED
        return await self._projects.update(project)

    async def delete(self, user: User, project_id: UUID) -> None:
        await require_project(
            self._projects, self._workspaces, project_id, user, WorkspaceRole.OWNER
        )
        await self._projects.delete(project_id)
