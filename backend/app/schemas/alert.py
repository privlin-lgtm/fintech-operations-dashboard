from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.models.enums import AlertSeverity, AlertStatus, AlertType, CasePriority, CaseType
from app.schemas.base import ORMModel, TimestampSchema, UUIDSchema

AlertSortField = Literal[
    "created_at",
    "-created_at",
    "severity",
    "-severity",
    "status",
    "-status",
]


class AlertRead(UUIDSchema, TimestampSchema):
    customer_id: UUID
    transaction_id: UUID | None = None
    case_id: UUID | None = None
    assignee_id: UUID | None = None
    alert_type: str
    severity: str
    status: str
    triggering_reason: str
    dismissal_reason: str | None = None
    resolved_at: datetime | None = None


class AlertCreate(ORMModel):
    customer_id: UUID
    alert_type: AlertType
    severity: AlertSeverity
    triggering_reason: str = Field(min_length=1, max_length=2_000)
    transaction_id: UUID | None = None
    assignee_id: UUID | None = None


class AlertUpdate(ORMModel):
    severity: AlertSeverity | None = None
    triggering_reason: str | None = Field(default=None, min_length=1, max_length=2_000)


class AlertAssign(ORMModel):
    assignee_id: UUID


class AlertResolve(ORMModel):
    reason: str = Field(min_length=1, max_length=2_000)


class AlertEscalate(ORMModel):
    case_id: UUID | None = None
    create_case: bool = False
    case_type: CaseType = CaseType.FRAUD
    priority: CasePriority = CasePriority.HIGH


class AlertSearchParams(ORMModel):
    q: str | None = Field(default=None, max_length=100)
    customer_id: UUID | None = None
    assignee_id: UUID | None = None
    severity: AlertSeverity | None = None
    status: AlertStatus | None = None
    alert_type: AlertType | None = Field(default=None, alias="type")
    sort: AlertSortField = "-created_at"
    limit: int = Field(default=25, ge=1, le=200)
    cursor: str | None = None
