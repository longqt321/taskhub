"""Test RBAC: kiểm tra role qua dependency RequireRoles."""

import pytest

from app.api.deps import RequireRoles
from app.core.exceptions import ForbiddenError
from app.models import User, UserRole


def _user(role: UserRole) -> User:
    return User(
        email="a@example.com",
        full_name="A",
        hashed_password="x",
        role=role,
        is_active=True,
    )


async def test_member_passes_when_role_allowed() -> None:
    check = RequireRoles(UserRole.MEMBER)

    result = await check(_user(UserRole.MEMBER))

    assert result.role == UserRole.MEMBER


async def test_member_blocked_when_role_not_allowed() -> None:
    check = RequireRoles(UserRole.ADMIN)

    with pytest.raises(ForbiddenError):
        await check(_user(UserRole.MEMBER))


async def test_admin_bypasses_role_check() -> None:
    check = RequireRoles(UserRole.MEMBER)

    result = await check(_user(UserRole.ADMIN))

    assert result.role == UserRole.ADMIN
