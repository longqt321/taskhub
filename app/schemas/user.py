"""Schema request/response cho auth và users."""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator, model_validator

from app.core import messages
from app.core.constants import MAX_NAME_LENGTH, MAX_PASSWORD_BYTES, MIN_PASSWORD_LENGTH
from app.models.user import UserRole
from app.schemas.base import BaseSchema


def _check_password_bytes(value: str) -> str:
    """bcrypt chỉ dùng 72 byte đầu, cắt theo byte chứ không theo ký tự."""
    if len(value.encode()) > MAX_PASSWORD_BYTES:
        raise ValueError(messages.MSG_PASSWORD_TOO_LONG.format(max_bytes=MAX_PASSWORD_BYTES))
    return value


class UserCreate(BaseSchema):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_BYTES)

    _password_bytes = field_validator("password")(_check_password_bytes)


class UserRead(BaseSchema):
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserUpdate(BaseSchema):
    full_name: str | None = Field(default=None, min_length=1, max_length=MAX_NAME_LENGTH)
    password: str | None = Field(default=None, min_length=MIN_PASSWORD_LENGTH)
    # bắt buộc khi đổi password, để tự mình xác nhận lại
    current_password: str | None = Field(default=None, max_length=MAX_PASSWORD_BYTES)

    @field_validator("password")
    @classmethod
    def _check_password(cls, value: str | None) -> str | None:
        return None if value is None else _check_password_bytes(value)

    @model_validator(mode="after")
    def _check_password_change(self) -> UserUpdate:
        # full_name là NOT NULL, gửi null là lỗi client chứ không phải ý xoá
        if "full_name" in self.model_fields_set and self.full_name is None:
            raise ValueError(messages.MSG_FULL_NAME_CANNOT_BE_NULL)
        if self.password is not None and self.current_password is None:
            raise ValueError(messages.MSG_CURRENT_PASSWORD_REQUIRED)
        if self.password is None and self.current_password is not None:
            raise ValueError(messages.MSG_CURRENT_PASSWORD_WITHOUT_PASSWORD)
        return self


class UserAdminUpdate(BaseSchema):
    """Admin sửa user khác: đổi tên, đổi role, khoá/mở tài khoản."""

    full_name: str | None = Field(default=None, min_length=1, max_length=MAX_NAME_LENGTH)
    role: UserRole | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def _reject_null(self) -> UserAdminUpdate:
        for field in ("full_name", "role", "is_active"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_BYTES)

    _password_bytes = field_validator("password")(_check_password_bytes)


class RefreshRequest(BaseSchema):
    refresh_token: str


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
