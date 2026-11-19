"""Gửi thông báo nền khi task được gán cho người mới."""

from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)


def send_task_assigned_email(recipient_email: str, task_title: str, task_id: UUID) -> None:
    """Chạy trong BackgroundTasks sau khi response đã trả về."""
    logger.info(
        "Sending assignment email to %s for task %s (%s)",
        recipient_email,
        task_id,
        task_title,
    )
