"""Schema request/response cho auth và users."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    # bắt buộc khi đổi password, để tự mình xác nhận lại
    current_password: str | None = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def _check_password_change(self) -> UserUpdate:
        # full_name là NOT NULL, gửi null là lỗi client chứ không phải ý xoá
        if "full_name" in self.model_fields_set and self.full_name is None:
            raise ValueError("full_name cannot be null")
        if self.password is not None and self.current_password is None:
            raise ValueError("current_password là bắt buộc khi đổi password")
        if self.password is None and self.current_password is not None:
            raise ValueError("current_password chỉ có nghĩa khi đổi password")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
