"""Test health check và vài thứ cơ bản."""

from httpx import AsyncClient


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
