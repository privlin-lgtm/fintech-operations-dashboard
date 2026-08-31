from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import ORMModel, TimestampSchema, UUIDSchema


class ReportRead(UUIDSchema, TimestampSchema):
    report_type: str
    filters: dict[str, Any]
    cadence: str | None = None
    recipients: list[str]
    created_by: UUID
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None


class ReportScheduleCreate(ORMModel):
    report_type: str
    filters: dict[str, Any] = Field(default_factory=dict)
    cadence: str
    recipients: list[str] = Field(min_length=1)


class DashboardSummary(ORMModel):
    open_cases: int
    sla_at_risk: int
    new_alerts: int
    cases_closed_today: int


class CaseReportParams(ORMModel):
    from_date: datetime | None = Field(default=None, alias="from")
    to_date: datetime | None = Field(default=None, alias="to")
    group_by: str = "status"
