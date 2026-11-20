"""Cấu hình app, đọc từ biến môi trường và file .env."""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import DATABASE_SCHEME
from app.core.messages import MSG_INVALID_API_PREFIX, MSG_INVALID_DATABASE_URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "TaskHub"
    app_version: str = "0.1.0"
    environment: Literal["local", "staging", "production"] = "local"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Bắt buộc khai báo trong .env, không đặt default để khỏi lỡ trỏ nhầm DB.
    database_url: str

    @field_validator("api_v1_prefix")
    @classmethod
    def _check_api_prefix(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError(MSG_INVALID_API_PREFIX)
        return value.rstrip("/")

    @field_validator("database_url")
    @classmethod
    def _check_database_url(cls, value: str) -> str:
        if not value.startswith(DATABASE_SCHEME):
            raise ValueError(MSG_INVALID_DATABASE_URL)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
