from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base import ORMModel, TimestampSchema, UUIDSchema


class CaseNoteRead(UUIDSchema, TimestampSchema):
    case_id: UUID
    author_id: UUID
    body: str
    is_system: bool


class CaseRead(UUIDSchema, TimestampSchema):
    case_number: str
    customer_id: UUID
    owner_id: UUID | None = None
    case_type: str
    status: str
    priority: str
    sla_due_at: datetime | None = None
    resolution_code: str | None = None
    closing_summary: str | None = None
    closed_at: datetime | None = None


class CaseDetail(CaseRead):
    notes: list[CaseNoteRead] = []


class CaseCreate(ORMModel):
    customer_id: UUID
    case_type: str
    priority: str = "medium"
    owner_id: UUID | None = None


class CaseUpdate(ORMModel):
    status: str | None = None
    priority: str | None = None
    owner_id: UUID | None = None


class CaseNoteCreate(ORMModel):
    body: str = Field(min_length=1)


class CaseClose(ORMModel):
    resolution_code: str = Field(min_length=1)
    closing_summary: str = Field(min_length=1)
    status: str = Field(default="closed_resolved")


class CaseReassign(ORMModel):
    owner_id: UUID
    reason: str = Field(min_length=1)


class CaseLinkCreate(ORMModel):
    transaction_id: UUID | None = None
    alert_id: UUID | None = None


class CaseSearchParams(ORMModel):
    status: str | None = None
    priority: str | None = None
    assignee: UUID | None = None
    sla_risk: bool | None = None
    limit: int = Field(default=25, ge=1, le=200)
    cursor: str | None = None
