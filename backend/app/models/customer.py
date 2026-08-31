from typing import TYPE_CHECKING

from sqlalchemy import LargeBinary, Text
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.alert import Alert
    from app.models.case import Case


class Customer(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "customers"

    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str | None] = mapped_column(CITEXT, nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_of_birth_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    kyc_status: Mapped[str] = mapped_column(
        Text, nullable=False, default="unverified", server_default="unverified"
    )
    risk_tier: Mapped[str] = mapped_column(
        Text, nullable=False, default="low", server_default="low"
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="active", server_default="active"
    )

    accounts: Mapped[list["Account"]] = relationship("Account", back_populates="customer")
    cases: Mapped[list["Case"]] = relationship("Case", back_populates="customer")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="customer")
