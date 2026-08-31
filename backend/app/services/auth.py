from uuid import UUID

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_token,
    verify_mfa_code,
    verify_password,
    verify_token,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.audit_log import AuditLogRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse

# Sentinel resource_id for audit entries where there's no real resource to
# point at yet (e.g. a failed login against an email that matches no user).
_UNKNOWN_RESOURCE = UUID(int=0)


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo
        self.audit_repo = audit_repo

    async def authenticate(self, credentials: LoginRequest) -> User:
        user = await self.user_repo.get_by_email(credentials.email)

        if user is None or not verify_password(credentials.password, user.hashed_password):
            await self.audit_repo.record(
                actor_id=user.id if user else None,
                action="login_failed",
                resource_type="user",
                resource_id=user.id if user else _UNKNOWN_RESOURCE,
                metadata={"email": credentials.email, "reason": "bad_credentials"},
            )
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is deactivated")

        if user.mfa_enabled:
            if not credentials.mfa_code:
                raise AuthenticationError("MFA code required")
            if not verify_mfa_code(user.mfa_secret or "", credentials.mfa_code):
                await self.audit_repo.record(
                    actor_id=user.id,
                    action="login_failed",
                    resource_type="user",
                    resource_id=user.id,
                    metadata={"reason": "bad_mfa_code"},
                )
                raise AuthenticationError("Invalid MFA code")

        return user

    async def login(self, credentials: LoginRequest) -> TokenResponse:
        user = await self.authenticate(credentials)
        await self.user_repo.update_last_login(user)
        response = await self._issue_tokens(user)
        await self.audit_repo.record(
            actor_id=user.id, action="login", resource_type="user", resource_id=user.id
        )
        return response

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = verify_token(refresh_token, expected_type="refresh")
        except ValueError as exc:
            raise AuthenticationError(str(exc)) from exc

        stored = await self.refresh_token_repo.get_by_hash(hash_token(refresh_token))
        if stored is None or not stored.is_active:
            raise AuthenticationError("Refresh token has been revoked or has expired")

        user = await self.user_repo.get_active_by_id(UUID(payload["sub"]))
        if user is None:
            raise AuthenticationError("User not found or inactive")

        # Rotate: this refresh token is single-use. A reused (already-revoked)
        # token can never mint a new pair, which is what makes a stolen-and-
        # replayed refresh token detectable rather than silently working.
        await self.refresh_token_repo.revoke(stored)
        return await self._issue_tokens(user)

    async def logout(self, refresh_token: str, actor: User) -> None:
        stored = await self.refresh_token_repo.get_by_hash(hash_token(refresh_token))
        if stored is not None and stored.user_id == actor.id:
            await self.refresh_token_repo.revoke(stored)

        # Bumping token_version invalidates every access token already issued
        # to this user, not just the one on this request — logout means
        # logged out, not "logged out on this device in ~30 minutes."
        await self.user_repo.bump_token_version(actor)
        await self.audit_repo.record(
            actor_id=actor.id, action="logout", resource_type="user", resource_id=actor.id
        )

    async def _issue_tokens(self, user: User) -> TokenResponse:
        claims = {"role": user.role.name, "tv": user.token_version}
        access_token = create_access_token(user.id, extra_claims=claims)
        refresh_token, _jti, expires_at = create_refresh_token(user.id)
        await self.refresh_token_repo.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_token(refresh_token),
                expires_at=expires_at,
            )
        )
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
