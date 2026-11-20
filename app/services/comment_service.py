"""Nghiệp vụ của comment trên task."""

from collections.abc import Sequence
from uuid import UUID

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.messages import MSG_COMMENT_DELETE_FORBIDDEN, MSG_COMMENT_NOT_FOUND
from app.models.comment import Comment
from app.models.user import User, UserRole
from app.models.workspace import WorkspaceRole
from app.repositories.comment_repository import CommentRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.schemas.comment import CommentCreate
from app.services.access import load_task


class CommentService:
    def __init__(
        self,
        comments: CommentRepository,
        tasks: TaskRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
    ) -> None:
        self._comments = comments
        self._tasks = tasks
        self._projects = projects
        self._workspaces = workspaces

    async def list(self, user: User, task_id: UUID) -> Sequence[Comment]:
        await load_task(
            self._tasks, self._projects, self._workspaces, task_id, user, WorkspaceRole.VIEWER
        )
        return await self._comments.list_in_task(task_id)

    async def create(self, user: User, task_id: UUID, data: CommentCreate) -> Comment:
        await load_task(
            self._tasks, self._projects, self._workspaces, task_id, user, WorkspaceRole.VIEWER
        )
        comment = Comment(task_id=task_id, author_id=user.id, content=data.content)
        created = await self._comments.add(comment)
        # trả kèm author để response không phải query thêm
        created.author = user
        return created

    async def delete(self, user: User, task_id: UUID, comment_id: UUID) -> None:
        await load_task(
            self._tasks, self._projects, self._workspaces, task_id, user, WorkspaceRole.VIEWER
        )
        comment = await self._comments.get(comment_id)
        if comment is None or comment.task_id != task_id:
            raise NotFoundError(MSG_COMMENT_NOT_FOUND, details={"comment_id": str(comment_id)})
        if not await self._can_delete(user, comment):
            raise ForbiddenError(MSG_COMMENT_DELETE_FORBIDDEN)
        await self._comments.delete(comment_id)

    async def _can_delete(self, user: User, comment: Comment) -> bool:
        """Tác giả xoá comment của mình, OWNER workspace xoá được mọi comment, ADMIN đi qua."""
        if user.role is UserRole.ADMIN or comment.author_id == user.id:
            return True
        task = await self._tasks.get(comment.task_id)
        if task is None:  # pragma: no cover - comment luôn thuộc task còn tồn tại
            return False
        project = await self._projects.get(task.project_id)
        if project is None:  # pragma: no cover
            return False
        member = await self._workspaces.get_member(project.workspace_id, user.id)
        return member is not None and member.role is WorkspaceRole.OWNER
