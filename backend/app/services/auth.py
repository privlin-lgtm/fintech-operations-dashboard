from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.user_repo = UserRepository(session)

    async def authenticate(self, credentials: LoginRequest) -> User:
        user = await self.user_repo.get_by_email(credentials.email)
        if user is None or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )
        return user

    async def login(self, credentials: LoginRequest) -> TokenResponse:
        user = await self.authenticate(credentials)
        await self.user_repo.update_last_login(user)
        return self._build_token_response(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = verify_token(refresh_token, expected_type="refresh")
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
            ) from exc

        user = await self.user_repo.get_active_by_id(UUID(payload["sub"]))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        return self._build_token_response(user)

    def _build_token_response(self, user: User) -> TokenResponse:
        claims = {
            "role": user.role.name,
            "permissions": user.role.permissions,
        }
        return TokenResponse(
            access_token=create_access_token(user.id, extra_claims=claims),
            refresh_token=create_refresh_token(user.id),
        )
