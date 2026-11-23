"""Test health check và vài thứ cơ bản."""

from httpx import AsyncClient
from pytest import MonkeyPatch


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_openapi_schema_is_served(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/tasks" in response.json()["paths"]


async def test_unknown_route_returns_json_error(client: AsyncClient) -> None:
    response = await client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"


async def test_openapi_has_bearer_scheme_and_tags(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    spec = response.json()
    schemes = spec["components"]["securitySchemes"]
    assert "HTTPBearer" in schemes
    assert schemes["HTTPBearer"]["type"] == "http"
    assert schemes["HTTPBearer"]["scheme"] == "bearer"
    tag_names = {tag["name"] for tag in spec["tags"]}
    expected = {"health", "auth", "users", "workspaces", "projects", "tasks", "labels", "comments"}
    assert expected <= tag_names

    used_tags = {
        tag
        for path_item in spec["paths"].values()
        for op in path_item.values()
        if isinstance(op, dict)
        for tag in op.get("tags", [])
    }
    assert used_tags <= tag_names

    assert spec["paths"]["/api/v1/users/me"]["get"].get("security")
    assert "security" not in spec["paths"]["/api/v1/auth/login"]["post"]


async def test_openapi_disabled_in_production(monkeypatch: MonkeyPatch) -> None:
    from httpx import ASGITransport

    from app.core.config import get_settings
    from app.main import create_app

    monkeypatch.setenv("ENVIRONMENT", "production")
    get_settings.cache_clear()
    try:
        prod_app = create_app()
        async with AsyncClient(
            transport=ASGITransport(app=prod_app), base_url="http://test"
        ) as prod_client:
            assert (await prod_client.get("/docs")).status_code == 404
            assert (await prod_client.get("/redoc")).status_code == 404
            assert (await prod_client.get("/openapi.json")).status_code == 404
    finally:
        monkeypatch.delenv("ENVIRONMENT", raising=False)
        get_settings.cache_clear()
