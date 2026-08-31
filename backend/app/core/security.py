import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pyotp
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.bcrypt_rounds
)


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: UUID | str,
    *,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    subject: UUID | str,
    *,
    expires_delta: timedelta | None = None,
) -> tuple[str, str, datetime]:
    """Returns (token, jti, expires_at). The caller persists a hash of the
    token keyed by jti so it can be looked up and revoked server-side — the
    JWT signature alone can't be un-issued once minted."""
    jti = str(uuid4())
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(days=settings.jwt_refresh_token_expire_days)
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "refresh",
        "jti": jti,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expire


def hash_token(token: str) -> str:
    """One-way hash for persisting a refresh token server-side. Not for
    passwords — the token is 128+ bits of random signed entropy, not a
    low-entropy secret a user picked, so a per-token salt isn't needed."""
    return hashlib.sha256(token.encode()).hexdigest()


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def verify_token(token: str, *, expected_type: str = "access") -> dict[str, Any]:
    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

    token_type = payload.get("type")
    if token_type != expected_type:
        raise ValueError(f"Expected {expected_type} token, got {token_type!r}")

    subject = payload.get("sub")
    if not subject:
        raise ValueError("Token missing subject claim")

    return payload


def generate_mfa_secret() -> str:
    """A base32 TOTP secret for enrollment. No enrollment endpoint exists yet —
    this is here so adding one later doesn't require touching this module."""
    return pyotp.random_base32()


def verify_mfa_code(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def generate_opaque_token() -> str:
    return secrets.token_urlsafe(32)
