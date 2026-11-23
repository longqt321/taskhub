"""Entrypoint của app."""

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.lifespan import lifespan
from app.core.logging import configure_logging

_OPENAPI_TAGS = [
    {"name": "health", "description": "Kiểm tra trạng thái hoạt động của service"},
    {"name": "auth", "description": "Đăng ký, đăng nhập, refresh token và logout"},
    {"name": "users", "description": "Profile cá nhân và thao tác quản trị user (ADMIN)"},
    {"name": "workspaces", "description": "Quản lý workspace và thành viên"},
    {"name": "projects", "description": "Quản lý project trong workspace"},
    {"name": "tasks", "description": "Quản lý task và lọc theo nhiều tiêu chí"},
    {"name": "labels", "description": "Quản lý label của project và gắn/bỏ khỏi task"},
    {"name": "comments", "description": "Bình luận trên task"},
]


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    is_prod = settings.environment == "production"

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "TaskHub - Task Management API. "
            "Các endpoint có biểu tượng ổ khoá yêu cầu `Authorization: Bearer <access_token>`."
        ),
        openapi_tags=_OPENAPI_TAGS,
        swagger_ui_parameters={"persistAuthorization": True},
        lifespan=lifespan,
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
