from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.role import Role


class User(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(CITEXT, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Bumped on logout/deactivation; embedded in every access token as "tv" so
    # a previously-issued token can be invalidated on the next request instead
    # of waiting out its remaining lifetime (up to jwt_access_token_expire_minutes).
    token_version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default="0")
    # Login lockout: consecutive failures since the last success, and how long
    # the account stays locked once the threshold is crossed (exponential
    # backoff — see core/config.py's login_lockout_* settings).
    failed_login_attempts: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="active",
        server_default="active",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="users",
        lazy="selectin",
    )

    @property
    def is_active(self) -> bool:
        return self.status == "active" and not self.is_deleted
