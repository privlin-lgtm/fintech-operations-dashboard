from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.user import User
from app.repositories.base import BaseRepository

settings = get_settings()


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.role))
            .where(User.email == email, User.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_id(self, user_id: UUID) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.role))
            .where(
                User.id == user_id,
                User.deleted_at.is_(None),
                User.status == "active",
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_last_login(self, user: User) -> User:
        user.last_login_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def bump_token_version(self, user: User) -> User:
        """Invalidates every access token already issued to this user — the
        'tv' claim they carry stops matching on the very next request."""
        user.token_version += 1
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def record_failed_login(self, user: User) -> None:
        """Exponential backoff once the threshold is crossed: base * 2^(n -
        threshold), capped — a few failures behave normally, sustained
        guessing gets slower with every additional attempt instead of a flat
        lockout window an attacker can just wait out."""
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.login_lockout_threshold:
            overage = user.failed_login_attempts - settings.login_lockout_threshold
            delay = min(
                settings.login_lockout_base_seconds * (2**overage),
                settings.login_lockout_max_seconds,
            )
            user.locked_until = datetime.now(UTC) + timedelta(seconds=delay)
        await self.session.flush()

    async def reset_failed_login(self, user: User) -> None:
        if user.failed_login_attempts or user.locked_until:
            user.failed_login_attempts = 0
            user.locked_until = None
            await self.session.flush()
