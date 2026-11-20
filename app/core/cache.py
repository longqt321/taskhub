"""Cache Redis cho danh sách task theo project, lỗi Redis thì bỏ qua để app vẫn chạy."""

from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.constants import DEFAULT_CACHE_TTL_SECONDS, PROJECT_TASKS_CACHE_PREFIX
from app.core.logging import get_logger
from app.core.pagination import PaginationParams
from app.repositories.task_repository import TaskFilters

logger = get_logger(__name__)


def _version_key(project_id: UUID) -> str:
    return f"{PROJECT_TASKS_CACHE_PREFIX}:{project_id}:ver"


def build_project_tasks_key(
    project_id: UUID,
    version: int,
    pagination: PaginationParams,
    filters: TaskFilters,
) -> str:
    """Mỗi tổ hợp project, version, trang và bộ lọc có một key riêng."""
    status_part = ",".join(item.value for item in filters.status) if filters.status else ""
    priority_part = ",".join(item.value for item in filters.priority) if filters.priority else ""
    parts = [
        f"{PROJECT_TASKS_CACHE_PREFIX}:{project_id}",
        f"v={version}",
        f"p={pagination.page}",
        f"l={pagination.limit}",
        f"a={filters.assignee_id or ''}",
        f"s={status_part}",
        f"pr={priority_part}",
        f"db={filters.due_before.isoformat() if filters.due_before else ''}",
        f"da={filters.due_after.isoformat() if filters.due_after else ''}",
        f"q={filters.search or ''}",
    ]
    return ":".join(parts)


class TaskCache:
    def __init__(self, client: Redis | None, ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS) -> None:
        self._client = client
        self._ttl = ttl_seconds

    async def get_version(self, project_id: UUID) -> int:
        if self._client is None:
            return 0
        try:
            raw = await self._client.get(_version_key(project_id))
            return int(raw) if raw is not None else 0
        except RedisError, ValueError:
            logger.warning("Redis get_version failed for project %s", project_id, exc_info=True)
            return 0

    async def get(self, key: str, project_id: UUID) -> str | None:
        if self._client is None:
            return None
        try:
            value = await self._client.get(key)
            return value if isinstance(value, str) else None
        except RedisError:
            logger.warning("Redis get failed for project %s", project_id, exc_info=True)
            return None

    async def set(self, key: str, value: str, project_id: UUID) -> None:
        if self._client is None:
            return
        try:
            await self._client.set(key, value, ex=self._ttl)
        except RedisError:
            logger.warning("Redis set failed for project %s", project_id, exc_info=True)

    async def invalidate_project(self, project_id: UUID) -> None:
        if self._client is None:
            return
        try:
            await self._client.incr(_version_key(project_id))
        except RedisError:
            logger.warning("Redis invalidate failed for project %s", project_id, exc_info=True)
