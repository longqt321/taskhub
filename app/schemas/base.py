"""Base schema dùng chung: strip khoảng trắng và đọc được từ ORM object."""

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True)
