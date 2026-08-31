from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.models.enums import (
    TransactionChannel,
    TransactionDirection,
    TransactionStatus,
)
from app.schemas.base import ORMModel, TimestampSchema, UUIDSchema

TransactionSortField = Literal[
    "created_at",
    "-created_at",
    "amount_cents",
    "-amount_cents",
    "status",
    "-status",
    "risk_score",
    "-risk_score",
]


class TransactionAccountSummary(ORMModel):
    id: UUID
    customer_id: UUID
    masked_number: str
    account_type: str


class TransactionStatusEvent(ORMModel):
    status: str
    occurred_at: datetime


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
    has_open_alert: bool = False
    has_open_case: bool = False


class TransactionDetail(TransactionRead):
    account: TransactionAccountSummary
    status_history: list[TransactionStatusEvent] = []
    open_alert_count: int = 0
    open_case_count: int = 0


class TransactionSearchParams(ORMModel):
    q: str | None = Field(default=None, max_length=100)
    customer_id: UUID | None = None
    account_id: UUID | None = None
    from_date: datetime | None = Field(default=None, alias="from")
    to_date: datetime | None = Field(default=None, alias="to")
    min_amount: int | None = Field(default=None, ge=0)
    max_amount: int | None = Field(default=None, ge=0)
    status: TransactionStatus | None = None
    channel: TransactionChannel | None = None
    direction: TransactionDirection | None = None
    sort: TransactionSortField = "-created_at"
    limit: int = Field(default=25, ge=1, le=200)
    cursor: str | None = None
