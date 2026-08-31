from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base import ORMModel, TimestampSchema, UUIDSchema


class AlertRead(UUIDSchema, TimestampSchema):
    customer_id: UUID
    transaction_id: UUID | None = None
    case_id: UUID | None = None
    alert_type: str
    severity: str
    status: str
    triggering_reason: str
    dismissal_reason: str | None = None
    resolved_at: datetime | None = None


class AlertDismiss(ORMModel):
    reason: str = Field(min_length=1)


class AlertEscalate(ORMModel):
    case_id: UUID | None = None
    create_case: bool = False
    case_type: str = "fraud"
    priority: str = "high"


class AlertSearchParams(ORMModel):
    severity: str | None = None
    status: str | None = None
    alert_type: str | None = Field(default=None, alias="type")
    limit: int = Field(default=25, ge=1, le=200)
    cursor: str | None = None
