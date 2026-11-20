"""Label của project và bảng nối label với task."""

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import MAX_COLOR_LENGTH, MAX_LABEL_LENGTH
from app.models.base import Base


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(MAX_LABEL_LENGTH))
    color: Mapped[str] = mapped_column(String(MAX_COLOR_LENGTH))


class TaskLabel(Base):
    __tablename__ = "task_labels"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    label_id: Mapped[UUID] = mapped_column(
        ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True
    )
