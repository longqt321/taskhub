"""Nghiệp vụ của resource tasks."""

from collections.abc import Callable, Sequence
from uuid import UUID

from app.core.cache import TaskCache
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

AssignCallback = Callable[[str, str, UUID], None]


class TaskService:
    def __init__(
        self,
        tasks: TaskRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        users: UserRepository,
        cache: TaskCache | None = None,
    ) -> None:
        self._tasks = tasks
        self._projects = projects
        self._workspaces = workspaces
        self._users = users
        self._cache = cache

    async def create(
        self,
        user: User,
        data: TaskCreate,
        on_assigned: AssignCallback | None = None,
    ) -> TaskModel:
        await require_project(
            self._projects, self._workspaces, data.project_id, user, WorkspaceRole.EDITOR
        )
        assignee = await self._check_assignee(data.assignee_id)
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
        created = await self._tasks.add(task)
        if self._cache is not None:
            await self._cache.invalidate_project(created.project_id)
        if assignee is not None and on_assigned is not None:
            on_assigned(assignee.email, created.title, created.id)
        return created

    async def get(self, user: User, task_id: UUID) -> TaskModel:
        return await load_task(
            self._tasks, self._projects, self._workspaces, task_id, user, WorkspaceRole.VIEWER
        )

    async def ensure_can_read_project(self, user: User, project_id: UUID) -> None:
        await require_project(
            self._projects, self._workspaces, project_id, user, WorkspaceRole.VIEWER
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

    async def update(
        self,
        user: User,
        task_id: UUID,
        data: TaskUpdate,
        on_assigned: AssignCallback | None = None,
    ) -> TaskModel:
        task = await load_task(
            self._tasks, self._projects, self._workspaces, task_id, user, WorkspaceRole.EDITOR
        )
        changes = data.model_dump(exclude_unset=True)
        previous_assignee = task.assignee_id
        assignee: User | None = None
        if "assignee_id" in changes:
            assignee = await self._check_assignee(changes["assignee_id"])
        for field, value in changes.items():
            setattr(task, field, value)
        updated = await self._tasks.update(task)
        if self._cache is not None:
            await self._cache.invalidate_project(updated.project_id)
        # chỉ gửi khi đổi sang người nhận mới, tránh gửi lặp khi sửa field khác
        if (
            assignee is not None
            and updated.assignee_id != previous_assignee
            and on_assigned is not None
        ):
            on_assigned(assignee.email, updated.title, updated.id)
        return updated

    async def delete(self, user: User, task_id: UUID) -> None:
        task = await load_task(
            self._tasks, self._projects, self._workspaces, task_id, user, WorkspaceRole.EDITOR
        )
        await self._tasks.delete(task_id)
        if self._cache is not None:
            await self._cache.invalidate_project(task.project_id)

    async def _check_assignee(self, assignee_id: UUID | None) -> User | None:
        if assignee_id is None:
            return None
        assignee = await self._users.get(assignee_id)
        if assignee is None:
            raise NotFoundError(MSG_ASSIGNEE_NOT_FOUND, details={"assignee_id": str(assignee_id)})
        return assignee
