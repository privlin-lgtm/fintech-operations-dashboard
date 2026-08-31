from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    mfa_code: str | None = Field(default=None, min_length=6, max_length=6)


class TokenResponse(BaseModel):
    """The refresh token is deliberately not a field here — it only ever
    travels as an httpOnly cookie (see endpoints/auth.py), never in a body
    JavaScript could read."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    type: str
    role: str | None = None
    tv: int | None = None
    jti: str | None = None
