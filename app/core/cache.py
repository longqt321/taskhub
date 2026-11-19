"""Cache Redis cho danh sách task theo project, lỗi Redis thì bỏ qua để app vẫn chạy."""

from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.logging import get_logger
from app.core.pagination import PaginationParams
from app.repositories.task_repository import TaskFilters

logger = get_logger(__name__)


def build_project_tasks_key(
    project_id: UUID, pagination: PaginationParams, filters: TaskFilters
) -> str:
    """Mỗi tổ hợp project, trang và bộ lọc có một key riêng để không trả nhầm kết quả."""
    parts = [
        f"tasks:project:{project_id}",
        f"p={pagination.page}",
        f"l={pagination.limit}",
        f"a={filters.assignee_id or ''}",
        f"s={filters.status.value if filters.status else ''}",
        f"pr={filters.priority.value if filters.priority else ''}",
        f"db={filters.due_before.isoformat() if filters.due_before else ''}",
        f"da={filters.due_after.isoformat() if filters.due_after else ''}",
        f"q={filters.search or ''}",
    ]
    return ":".join(parts)


class TaskCache:
    def __init__(self, client: Redis | None, ttl_seconds: int = 60) -> None:
        self._client = client
        self._ttl = ttl_seconds

    async def get(self, key: str) -> str | None:
        if self._client is None:
            return None
        try:
            value = await self._client.get(key)
            return value if isinstance(value, str) else None
        except RedisError:
            logger.warning("Redis get failed for key %s", key)
            return None

    async def set(self, key: str, value: str) -> None:
        if self._client is None:
            return
        try:
            await self._client.set(key, value, ex=self._ttl)
        except RedisError:
            logger.warning("Redis set failed for key %s", key)

    async def invalidate_project(self, project_id: UUID) -> None:
        if self._client is None:
            return
        pattern = f"tasks:project:{project_id}:*"
        try:
            keys = [key async for key in self._client.scan_iter(match=pattern)]
            if keys:
                await self._client.delete(*keys)
        except RedisError:
            logger.warning("Redis invalidate failed for project %s", project_id)
