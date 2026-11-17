"""Repository cho user và refresh token."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import RefreshToken, User, UserRole
from app.repositories.sqlalchemy_repo import SqlAlchemyRepository


class UserRepository(SqlAlchemyRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.scalars(select(User).where(User.email == email))
        return result.first()

    async def count_active_admins(self) -> int:
        """Đếm admin đang hoạt động, dùng để chặn xoá admin cuối cùng."""
        total = await self._session.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role == UserRole.ADMIN, User.is_active.is_(True))
        )
        return total or 0


class RefreshTokenRepository(SqlAlchemyRepository[RefreshToken]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, RefreshToken)

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        result = await self._session.scalars(select(RefreshToken).where(RefreshToken.jti == jti))
        return result.first()

    async def _revoke_uncommitted(self, jti: str) -> bool:
        """UPDATE ... WHERE revoked_at IS NULL RETURNING id, để hai request song song
        cùng refresh bằng một token thì chỉ một request đổi được dòng."""
        result = await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.jti == jti, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
            .returning(RefreshToken.id)
        )
        return result.scalar_one_or_none() is not None

    async def revoke(self, jti: str) -> bool:
        revoked = await self._revoke_uncommitted(jti)
        await self._session.commit()
        return revoked

    async def rotate(self, old_jti: str, new_token: RefreshToken) -> bool:
        """Thu hồi token cũ và ghi token mới trong cùng một transaction."""
        if not await self._revoke_uncommitted(old_jti):
            await self._session.rollback()
            return False
        self._session.add(new_token)
        await self._session.commit()
        return True

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        await self._session.commit()
