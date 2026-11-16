"""Fixtures dùng chung."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_task_repository
from app.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    # cache_clear để mỗi test có store in-memory riêng, sạch
    get_task_repository.cache_clear()
    # raise_app_exceptions=False để test được response 500 thay vì exception ném ra
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
