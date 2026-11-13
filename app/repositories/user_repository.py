"""Repository cho user và refresh token."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import RefreshToken, User
from app.repositories.sqlalchemy_repo import SqlAlchemyRepository


class UserRepository(SqlAlchemyRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.scalars(select(User).where(User.email == email))
        return result.first()


class RefreshTokenRepository(SqlAlchemyRepository[RefreshToken]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, RefreshToken)

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        result = await self._session.scalars(select(RefreshToken).where(RefreshToken.jti == jti))
        return result.first()

    async def revoke(self, jti: str) -> bool:
        token = await self.get_by_jti(jti)
        if token is None or token.revoked_at is not None:
            return False
        token.revoked_at = datetime.now(UTC)
        await self._session.commit()
        return True

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        result = await self._session.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
            )
        )
        now = datetime.now(UTC)
        for token in result.all():
            token.revoked_at = now
        await self._session.commit()
