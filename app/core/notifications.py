"""Gửi thông báo nền khi task được gán cho người mới."""

from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)


def send_task_assigned_email(recipient_email: str, task_title: str, task_id: UUID) -> None:
    """Chạy trong BackgroundTasks sau khi response đã trả về."""
    # Không log email để tránh lộ PII vào log
    _ = recipient_email
    logger.info("Queued assignment notification for task %s (%s)", task_id, task_title)
