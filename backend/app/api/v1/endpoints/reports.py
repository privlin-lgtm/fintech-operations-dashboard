from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response

from app.core.dependencies import ReportServiceDep, require_roles
from app.models.user import User
from app.schemas.report import (
    AlertVolumeReport,
    CaseVolumeReport,
    DashboardSummary,
    ExportFormat,
    ReportRead,
    ReportScheduleCreate,
    SlaPerformanceReport,
    TransactionVolumeReport,
)

router = APIRouter(prefix="/reports", tags=["reports"])

REPORT_READ_ROLES = ("analyst", "investigator", "team_lead", "compliance_auditor", "admin")
REPORT_SCHEDULE_ROLES = ("team_lead", "compliance_auditor", "admin")
ReportReaderDep = Annotated[User, Depends(require_roles(*REPORT_READ_ROLES))]
ReportSchedulerDep = Annotated[User, Depends(require_roles(*REPORT_SCHEDULE_ROLES))]

TransactionGroupBy = Literal["day", "status", "channel", "direction"]
CaseGroupBy = Literal["day", "status", "priority", "case_type"]
AlertGroupBy = Literal["day", "status", "severity", "alert_type"]
SlaGroupBy = Literal["priority", "case_type"]


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard(_user: ReportReaderDep, service: ReportServiceDep) -> DashboardSummary:
    return await service.dashboard()


@router.get("/transactions", response_model=None)
async def get_transaction_report(
    _user: ReportReaderDep,
    service: ReportServiceDep,
    from_date: Annotated[datetime | None, Query(alias="from")] = None,
    to_date: Annotated[datetime | None, Query(alias="to")] = None,
    group_by: Annotated[TransactionGroupBy, Query()] = "day",
    export_format: Annotated[ExportFormat, Query(alias="format")] = "json",
) -> TransactionVolumeReport | Response:
    report = await service.transaction_report(
        from_date=from_date, to_date=to_date, group_by=group_by
    )
    exported = service.render_volume_export(
        title="Daily Transactions Report",
        filename="daily-transactions.pdf",
        export_format=export_format,
        columns=["group", "count", "total_amount_cents"],
        rows=[row.model_dump() for row in report.rows],
    )
    return exported or report


@router.get("/cases", response_model=None)
async def get_case_report(
    _user: ReportReaderDep,
    service: ReportServiceDep,
    from_date: Annotated[datetime | None, Query(alias="from")] = None,
    to_date: Annotated[datetime | None, Query(alias="to")] = None,
    group_by: Annotated[CaseGroupBy, Query()] = "status",
    export_format: Annotated[ExportFormat, Query(alias="format")] = "json",
) -> CaseVolumeReport | Response:
    report = await service.case_report(
        from_date=from_date, to_date=to_date, group_by=group_by
    )
    exported = service.render_volume_export(
        title="Case Volume Report",
        filename="case-volume.pdf",
        export_format=export_format,
        columns=["group", "count"],
        rows=[row.model_dump() for row in report.rows],
    )
    return exported or report


@router.get("/alerts", response_model=None)
async def get_alert_report(
    _user: ReportReaderDep,
    service: ReportServiceDep,
    from_date: Annotated[datetime | None, Query(alias="from")] = None,
    to_date: Annotated[datetime | None, Query(alias="to")] = None,
    group_by: Annotated[AlertGroupBy, Query()] = "status",
    export_format: Annotated[ExportFormat, Query(alias="format")] = "json",
) -> AlertVolumeReport | Response:
    report = await service.alert_report(
        from_date=from_date, to_date=to_date, group_by=group_by
    )
    exported = service.render_volume_export(
        title="Alert Volume Report",
        filename="alert-volume.pdf",
        export_format=export_format,
        columns=["group", "count"],
        rows=[row.model_dump() for row in report.rows],
    )
    return exported or report


@router.get("/sla", response_model=None)
async def get_sla_report(
    _user: ReportReaderDep,
    service: ReportServiceDep,
    from_date: Annotated[datetime | None, Query(alias="from")] = None,
    to_date: Annotated[datetime | None, Query(alias="to")] = None,
    group_by: Annotated[SlaGroupBy, Query()] = "priority",
    export_format: Annotated[ExportFormat, Query(alias="format")] = "json",
) -> SlaPerformanceReport | Response:
    report = await service.sla_report(
        from_date=from_date, to_date=to_date, group_by=group_by
    )
    exported = service.render_sla_export(report=report, export_format=export_format)
    return exported or report


@router.post("/schedules", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def create_report_schedule(
    data: ReportScheduleCreate, current_user: ReportSchedulerDep, service: ReportServiceDep
) -> ReportRead:
    return await service.create_schedule(data, current_user)
