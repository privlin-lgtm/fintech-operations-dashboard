from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.base import ORMModel, TimestampSchema, UUIDSchema


class RoleRead(UUIDSchema, TimestampSchema):
    name: str
    description: str | None = None
    permissions: dict


class UserBase(ORMModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8)
    role_id: UUID


class UserRead(UserBase, UUIDSchema, TimestampSchema):
    role_id: UUID
    mfa_enabled: bool
    status: str
    last_login_at: datetime | None = None
    role: RoleRead | None = None


class UserInDB(UserRead):
    hashed_password: str


class AssignableUser(ORMModel):
    """The minimum a person picker needs: who they are and what they do."""

    id: UUID
    full_name: str
    role: str
