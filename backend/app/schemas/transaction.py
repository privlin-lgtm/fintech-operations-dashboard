from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.schemas.base import ORMModel, TimestampSchema, UUIDSchema


class TransactionRead(UUIDSchema, TimestampSchema):
    account_id: UUID
    amount_cents: int
    currency: str
    direction: str
    channel: str
    status: str
    counterparty_masked: str | None = None
    risk_score: Decimal | None = None
    settled_at: datetime | None = None


class TransactionSearchParams(ORMModel):
    account_id: UUID | None = None
    from_date: datetime | None = Field(default=None, alias="from")
    to_date: datetime | None = Field(default=None, alias="to")
    min_amount: int | None = None
    max_amount: int | None = None
    status: str | None = None
    channel: str | None = None
    limit: int = Field(default=25, ge=1, le=200)
    cursor: str | None = None
