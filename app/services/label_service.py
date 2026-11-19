"""Nghiệp vụ của label: CRUD trong project và gán/bỏ khỏi task."""

from collections.abc import Sequence
from uuid import UUID

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.messages import (
    MSG_LABEL_ALREADY_ATTACHED,
    MSG_LABEL_ALREADY_EXISTS,
    MSG_LABEL_NOT_ATTACHED,
    MSG_LABEL_NOT_FOUND,
    MSG_LABEL_NOT_IN_PROJECT,
)
from app.models.label import Label
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.repositories.label_repository import LabelRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.label import LabelCreate, LabelUpdate
from app.services.access import load_task, require_project


class LabelService:
    def __init__(
        self,
        labels: LabelRepository,
        projects: ProjectRepository,
        tasks: TaskRepository,
        workspaces: WorkspaceRepository,
    ) -> None:
        self._labels = labels
        self._projects = projects
        self._tasks = tasks
        self._workspaces = workspaces

    async def create(self, user: User, project_id: UUID, data: LabelCreate) -> Label:
        await require_project(
            self._projects, self._workspaces, project_id, user, WorkspaceRole.EDITOR
        )
        if await self._labels.get_by_name(project_id, data.name) is not None:
            raise ConflictError(MSG_LABEL_ALREADY_EXISTS, details={"name": data.name})
        return await self._labels.add(
            Label(project_id=project_id, name=data.name, color=data.color)
        )

    async def list(self, user: User, project_id: UUID) -> Sequence[Label]:
        await require_project(
            self._projects, self._workspaces, project_id, user, WorkspaceRole.VIEWER
        )
        return await self._labels.list_in_project(project_id)

    async def update(self, user: User, label_id: UUID, data: LabelUpdate) -> Label:
        label = await self._get_label(label_id)
        await require_project(
            self._projects, self._workspaces, label.project_id, user, WorkspaceRole.EDITOR
        )
        changes = data.model_dump(exclude_unset=True)
        new_name = changes.get("name")
        if (
            new_name is not None
            and new_name != label.name
            and await self._labels.get_by_name(label.project_id, new_name) is not None
        ):
            raise ConflictError(MSG_LABEL_ALREADY_EXISTS, details={"name": new_name})
        for field, value in changes.items():
            setattr(label, field, value)
        return await self._labels.update(label)

    async def delete(self, user: User, label_id: UUID) -> None:
        label = await self._get_label(label_id)
        await require_project(
            self._projects, self._workspaces, label.project_id, user, WorkspaceRole.EDITOR
        )
        await self._labels.delete(label_id)

    async def list_for_task(self, user: User, task_id: UUID) -> Sequence[Label]:
        await load_task(
            self._tasks, self._projects, self._workspaces, task_id, user, WorkspaceRole.VIEWER
        )
        return await self._labels.list_for_task(task_id)

    async def attach(self, user: User, task_id: UUID, label_id: UUID) -> Sequence[Label]:
        task = await load_task(
            self._tasks, self._projects, self._workspaces, task_id, user, WorkspaceRole.EDITOR
        )
        label = await self._get_label(label_id)
        if label.project_id != task.project_id:
            raise BadRequestError(MSG_LABEL_NOT_IN_PROJECT, details={"label_id": str(label_id)})
        if await self._labels.is_attached(task_id, label_id):
            raise ConflictError(MSG_LABEL_ALREADY_ATTACHED, details={"label_id": str(label_id)})
        await self._labels.attach(task_id, label_id)
        return await self._labels.list_for_task(task_id)

    async def detach(self, user: User, task_id: UUID, label_id: UUID) -> Sequence[Label]:
        await load_task(
            self._tasks, self._projects, self._workspaces, task_id, user, WorkspaceRole.EDITOR
        )
        if not await self._labels.is_attached(task_id, label_id):
            raise NotFoundError(MSG_LABEL_NOT_ATTACHED, details={"label_id": str(label_id)})
        await self._labels.detach(task_id, label_id)
        return await self._labels.list_for_task(task_id)

    async def _get_label(self, label_id: UUID) -> Label:
        label = await self._labels.get(label_id)
        if label is None:
            raise NotFoundError(MSG_LABEL_NOT_FOUND, details={"label_id": str(label_id)})
        return label
