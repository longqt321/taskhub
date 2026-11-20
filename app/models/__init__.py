"""Gom import model để Alembic thấy đủ metadata."""

from app.models.base import Base
from app.models.comment import Comment
from app.models.label import Label, TaskLabel
from app.models.project import Project, ProjectStatus
from app.models.task import TaskModel, TaskPriority, TaskStatus
from app.models.user import RefreshToken, User, UserRole
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole

__all__ = [
    "Base",
    "Comment",
    "Label",
    "Project",
    "ProjectStatus",
    "RefreshToken",
    "TaskLabel",
    "TaskModel",
    "TaskPriority",
    "TaskStatus",
    "User",
    "UserRole",
    "Workspace",
    "WorkspaceMember",
    "WorkspaceRole",
]
