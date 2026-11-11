"""Schema request/response của resource items."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _reject_null_name(self) -> ItemUpdate:
        # name không cho null. Gửi null là lỗi client, không phải ý xoá field,
        # nên chặn ở đây để trả 422 thay vì ghi None vào entity rồi vỡ lúc response.
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null")
        return self


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
