"""Nghiệp vụ của resource tasks."""

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.core.messages import MSG_TASK_NOT_FOUND
from app.core.pagination import PaginationParams
from app.models.task import Task
from app.repositories.base import BaseRepository
from app.schemas.task import TaskCreate, TaskUpdate


def _not_found(task_id: UUID) -> NotFoundError:
    return NotFoundError(MSG_TASK_NOT_FOUND, details={"task_id": str(task_id)})


class TaskService:
    def __init__(self, repository: BaseRepository[Task]) -> None:
        self._repository = repository

    async def create(self, data: TaskCreate) -> Task:
        task = Task(title=data.title, description=data.description, status=data.status)
        return await self._repository.add(task)

    async def get(self, task_id: UUID) -> Task:
        task = await self._repository.get(task_id)
        if task is None:
            raise _not_found(task_id)
        return task

    async def list(self, pagination: PaginationParams) -> tuple[list[Task], int]:
        tasks, total = await self._repository.list(offset=pagination.offset, limit=pagination.limit)
        return list(tasks), total

    async def update(self, task_id: UUID, data: TaskUpdate) -> Task:
        task = await self.get(task_id)
        for field_name, value in data.model_dump(exclude_unset=True).items():
            setattr(task, field_name, value)
        return await self._repository.update(task)

    async def delete(self, task_id: UUID) -> None:
        if not await self._repository.delete(task_id):
            raise _not_found(task_id)
