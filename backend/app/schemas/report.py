from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from app.schemas.base import ORMModel, TimestampSchema, UUIDSchema

ExportFormat = Literal["json", "csv", "pdf"]


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


class ReportDateRangeParams(ORMModel):
    from_date: datetime | None = Field(default=None, alias="from")
    to_date: datetime | None = Field(default=None, alias="to")
    format: ExportFormat = "json"


class VolumeRow(ORMModel):
    group: str
    count: int


class TransactionVolumeRow(VolumeRow):
    total_amount_cents: int = 0


class TransactionVolumeReport(ORMModel):
    report_type: str = "daily_transactions"
    group_by: str
    rows: list[TransactionVolumeRow]
    total_count: int
    total_amount_cents: int


class CaseVolumeReport(ORMModel):
    report_type: str = "case_volume"
    group_by: str
    rows: list[VolumeRow]
    total_count: int


class AlertVolumeReport(ORMModel):
    report_type: str = "alert_volume"
    group_by: str
    rows: list[VolumeRow]
    total_count: int


class SlaBreakdownRow(ORMModel):
    group: str
    closed: int
    met_sla: int
    missed_sla: int


class SlaPerformanceReport(ORMModel):
    report_type: str = "sla_performance"
    group_by: str
    total_closed: int
    met_sla: int
    missed_sla: int
    currently_at_risk: int
    compliance_rate: float | None
    breakdown: list[SlaBreakdownRow]
