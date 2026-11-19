"""Nghiệp vụ của resource tasks."""

from collections.abc import Sequence
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.core.messages import MSG_ASSIGNEE_NOT_FOUND
from app.core.pagination import PaginationParams
from app.models.task import TaskModel
from app.models.user import User, UserRole
from app.models.workspace import WorkspaceRole
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskFilters, TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.access import load_task, require_project


class TaskService:
    def __init__(
        self,
        tasks: TaskRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        users: UserRepository,
    ) -> None:
        self._tasks = tasks
        self._projects = projects
        self._workspaces = workspaces
        self._users = users

    async def create(self, user: User, data: TaskCreate) -> TaskModel:
        await require_project(
            self._projects, self._workspaces, data.project_id, user, WorkspaceRole.EDITOR
        )
        await self._check_assignee(data.assignee_id)
        task = TaskModel(
            project_id=data.project_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            assignee_id=data.assignee_id,
            due_date=data.due_date,
            created_by=user.id,
            labels=[],
        )
        return await self._tasks.add(task)

    async def get(self, user: User, task_id: UUID) -> TaskModel:
        return await load_task(
            self._tasks, self._projects, self._workspaces, task_id, user, WorkspaceRole.VIEWER
        )

    async def list(
        self,
        user: User,
        pagination: PaginationParams,
        filters: TaskFilters,
        project_id: UUID | None = None,
    ) -> tuple[Sequence[TaskModel], int]:
        if project_id is not None:
            await require_project(
                self._projects, self._workspaces, project_id, user, WorkspaceRole.VIEWER
            )
            return await self._tasks.list_in_project(
                project_id, filters=filters, offset=pagination.offset, limit=pagination.limit
            )

        if user.role is UserRole.ADMIN:
            return await self._tasks.list_all(
                filters=filters, offset=pagination.offset, limit=pagination.limit
            )

        return await self._tasks.list_for_user(
            user.id, filters=filters, offset=pagination.offset, limit=pagination.limit
        )

    async def update(self, user: User, task_id: UUID, data: TaskUpdate) -> TaskModel:
        task = await load_task(
            self._tasks, self._projects, self._workspaces, task_id, user, WorkspaceRole.EDITOR
        )
        changes = data.model_dump(exclude_unset=True)
        if "assignee_id" in changes:
            await self._check_assignee(changes["assignee_id"])
        for field, value in changes.items():
            setattr(task, field, value)
        return await self._tasks.update(task)

    async def delete(self, user: User, task_id: UUID) -> None:
        await load_task(
            self._tasks, self._projects, self._workspaces, task_id, user, WorkspaceRole.EDITOR
        )
        await self._tasks.delete(task_id)

    async def _check_assignee(self, assignee_id: UUID | None) -> None:
        if assignee_id is None:
            return
        if await self._users.get(assignee_id) is None:
            raise NotFoundError(MSG_ASSIGNEE_NOT_FOUND, details={"assignee_id": str(assignee_id)})
