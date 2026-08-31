from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.customer import Customer
    from app.models.transaction import Transaction
    from app.models.user import User


class Case(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "cases"

    case_number: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    owner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    case_type: Mapped[str] = mapped_column("type", Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="new", server_default="new"
    )
    priority: Mapped[str] = mapped_column(
        Text, nullable=False, default="medium", server_default="medium"
    )
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    closing_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="cases")
    owner: Mapped["User | None"] = relationship("User", foreign_keys=[owner_id])
    notes: Mapped[list["CaseNote"]] = relationship(
        "CaseNote", back_populates="case", order_by="CaseNote.created_at"
    )
    transaction_links: Mapped[list["CaseTransactionLink"]] = relationship(
        "CaseTransactionLink", back_populates="case"
    )
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="case")


class CaseTransactionLink(Base):
    __tablename__ = "case_transaction_links"

    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True
    )
    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="RESTRICT"), primary_key=True
    )
    linked_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    case: Mapped["Case"] = relationship("Case", back_populates="transaction_links")
    transaction: Mapped["Transaction"] = relationship("Transaction")


class CaseNote(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "case_notes"

    case_id: Mapped[UUID] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    case: Mapped["Case"] = relationship("Case", back_populates="notes")
    author: Mapped["User"] = relationship("User")
