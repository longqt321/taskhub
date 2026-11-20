"""Schema request/response của workspace và thành viên."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import EmailStr, Field, model_validator

from app.core.constants import MAX_NAME_LENGTH
from app.core.messages import MSG_NAME_CANNOT_BE_NULL, MSG_OWNER_ROLE_RESERVED
from app.models.user import UserRole
from app.models.workspace import WorkspaceRole
from app.schemas.base import BaseSchema


class WorkspaceCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)


class WorkspaceUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=MAX_NAME_LENGTH)

    @model_validator(mode="after")
    def _reject_null_name(self) -> WorkspaceUpdate:
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError(MSG_NAME_CANNOT_BE_NULL)
        return self


class WorkspaceRead(BaseSchema):
    id: UUID
    name: str
    owner_id: UUID
    created_at: datetime


class MemberInvite(BaseSchema):
    email: EmailStr
    role: WorkspaceRole = WorkspaceRole.VIEWER

    @model_validator(mode="after")
    def _reject_owner_role(self) -> MemberInvite:
        # OWNER chỉ có một, là người tạo workspace, không mời bằng endpoint này.
        if self.role is WorkspaceRole.OWNER:
            raise ValueError(MSG_OWNER_ROLE_RESERVED)
        return self


class MemberRoleUpdate(BaseSchema):
    role: Literal[WorkspaceRole.EDITOR, WorkspaceRole.VIEWER]


class MemberUserRead(BaseSchema):
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole


class MemberRead(BaseSchema):
    user: MemberUserRead
    role: WorkspaceRole
    joined_at: datetime
