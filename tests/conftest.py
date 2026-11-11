"""Fixtures dùng chung."""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_item_repository
from app.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    # cache_clear để mỗi test có store in-memory riêng, sạch
    get_item_repository.cache_clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
