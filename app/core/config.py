"""Cấu hình app, đọc từ biến môi trường và file .env."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import DATABASE_SCHEME, MIN_SECRET_KEY_BYTES
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

    # JWT. secret_key phải đủ dài cho HS256, lấy giới hạn từ constants.
    secret_key: str
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=1)
    refresh_token_expire_days: int = Field(default=7, ge=1)

    @field_validator("secret_key")
    @classmethod
    def _check_secret_key(cls, value: str) -> str:
        if len(value.encode()) < MIN_SECRET_KEY_BYTES:
            raise ValueError(f"secret_key phải dài ít nhất {MIN_SECRET_KEY_BYTES} bytes")
        return value

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
