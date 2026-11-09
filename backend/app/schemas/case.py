from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.models.enums import CasePriority, CaseStatus, CaseType
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
    owner_name: str | None = None
    notes: list[CaseNoteRead] = []


class CaseCreate(ORMModel):
    customer_id: UUID
    case_type: CaseType
    priority: CasePriority = CasePriority.MEDIUM
    owner_id: UUID | None = None


class CaseUpdate(ORMModel):
    status: CaseStatus | None = None
    priority: CasePriority | None = None

    @field_validator("status")
    @classmethod
    def reject_closed_via_patch(cls, value: CaseStatus | None) -> CaseStatus | None:
        if value is not None and value.value.startswith("closed"):
            raise ValueError("Use POST /cases/{id}/close to close a case")
        return value


class CaseNoteCreate(ORMModel):
    body: str = Field(min_length=1, max_length=10_000)


class CaseAssign(ORMModel):
    owner_id: UUID


class CaseClose(ORMModel):
    resolution_code: str = Field(min_length=1, max_length=128)
    closing_summary: str = Field(min_length=1, max_length=10_000)
    status: CaseStatus = CaseStatus.CLOSED_RESOLVED

    @field_validator("status")
    @classmethod
    def must_be_closed_status(cls, value: CaseStatus) -> CaseStatus:
        if value.value not in ("closed_resolved", "closed_no_action"):
            raise ValueError("status must be closed_resolved or closed_no_action")
        return value


class CaseReassign(ORMModel):
    owner_id: UUID
    reason: str = Field(min_length=1, max_length=2_000)


class CaseLinkCreate(ORMModel):
    transaction_id: UUID | None = None
    alert_id: UUID | None = None

    @model_validator(mode="after")
    def require_at_least_one_link(self) -> "CaseLinkCreate":
        if self.transaction_id is None and self.alert_id is None:
            raise ValueError("Provide transaction_id and/or alert_id")
        return self


class CaseSearchParams(ORMModel):
    status: CaseStatus | None = None
    priority: CasePriority | None = None
    assignee: UUID | None = None
    sla_risk: bool | None = None
    limit: int = Field(default=25, ge=1, le=200)
    cursor: str | None = None
