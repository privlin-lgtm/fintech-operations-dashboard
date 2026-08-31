from datetime import datetime

from app.core.export import rows_to_csv, rows_to_pdf
from app.models.report import Report
from app.models.user import User
from app.repositories.alert import AlertRepository
from app.repositories.audit_log import AuditLogRepository
from app.repositories.report import ReportRepository
from app.schemas.report import (
    AlertVolumeReport,
    CaseVolumeReport,
    DashboardSummary,
    ExportFormat,
    ReportRead,
    ReportScheduleCreate,
    SlaPerformanceReport,
    TransactionVolumeReport,
    TransactionVolumeRow,
    VolumeRow,
)


class ReportService:
    def __init__(
        self,
        report_repo: ReportRepository,
        alert_repo: AlertRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self.repo = report_repo
        self.alert_repo = alert_repo
        self.audit_repo = audit_repo

    async def dashboard(self) -> DashboardSummary:
        return DashboardSummary(
            open_cases=await self.repo.count_open_cases(),
            sla_at_risk=await self.repo.count_sla_at_risk(),
            new_alerts=await self.alert_repo.count_by_status("new"),
            cases_closed_today=await self.repo.count_cases_closed_today(),
        )

    async def transaction_report(
        self,
        *,
        from_date: datetime | None,
        to_date: datetime | None,
        group_by: str,
    ) -> TransactionVolumeReport:
        rows = await self.repo.transaction_volume_by_group(
            from_date=from_date, to_date=to_date, group_by=group_by
        )
        typed_rows = [TransactionVolumeRow.model_validate(row) for row in rows]
        return TransactionVolumeReport(
            group_by=group_by,
            rows=typed_rows,
            total_count=sum(row.count for row in typed_rows),
            total_amount_cents=sum(row.total_amount_cents for row in typed_rows),
        )

    async def case_report(
        self,
        *,
        from_date: datetime | None,
        to_date: datetime | None,
        group_by: str,
    ) -> CaseVolumeReport:
        rows = await self.repo.case_volume_by_group(
            from_date=from_date, to_date=to_date, group_by=group_by
        )
        typed_rows = [VolumeRow.model_validate(row) for row in rows]
        return CaseVolumeReport(
            group_by=group_by,
            rows=typed_rows,
            total_count=sum(row.count for row in typed_rows),
        )

    async def alert_report(
        self,
        *,
        from_date: datetime | None,
        to_date: datetime | None,
        group_by: str,
    ) -> AlertVolumeReport:
        rows = await self.repo.alert_volume_by_group(
            from_date=from_date, to_date=to_date, group_by=group_by
        )
        typed_rows = [VolumeRow.model_validate(row) for row in rows]
        return AlertVolumeReport(
            group_by=group_by,
            rows=typed_rows,
            total_count=sum(row.count for row in typed_rows),
        )

    async def sla_report(
        self,
        *,
        from_date: datetime | None,
        to_date: datetime | None,
        group_by: str,
    ) -> SlaPerformanceReport:
        data = await self.repo.sla_performance(
            from_date=from_date, to_date=to_date, group_by=group_by
        )
        return SlaPerformanceReport(group_by=group_by, **data)

    async def create_schedule(
        self, data: ReportScheduleCreate, actor: User
    ) -> ReportRead:
        report = Report(
            report_type=data.report_type,
            filters=data.filters,
            cadence=data.cadence,
            recipients=data.recipients,
            created_by=actor.id,
        )
        created = await self.repo.add_schedule(report)
        await self.audit_repo.record(
            actor_id=actor.id,
            action="create",
            resource_type="report_schedule",
            resource_id=created.id,
        )
        return ReportRead.model_validate(created)

    def render_volume_export(
        self,
        *,
        title: str,
        filename: str,
        export_format: ExportFormat,
        columns: list[str],
        rows: list[dict],
    ):
        if export_format == "json":
            return None
        if export_format == "csv":
            return rows_to_csv(rows, columns)
        return rows_to_pdf(title=title, columns=columns, rows=rows, filename=filename)

    def render_sla_export(
        self,
        *,
        report: SlaPerformanceReport,
        export_format: ExportFormat,
    ):
        if export_format == "json":
            return None
        rows = [row.model_dump() for row in report.breakdown]
        columns = ["group", "closed", "met_sla", "missed_sla"]
        if export_format == "csv":
            summary_rows = [
                {
                    "group": "summary",
                    "closed": report.total_closed,
                    "met_sla": report.met_sla,
                    "missed_sla": report.missed_sla,
                },
                *rows,
            ]
            return rows_to_csv(summary_rows, columns)
        return rows_to_pdf(
            title="SLA Performance Report",
            columns=columns,
            rows=rows,
            filename="sla-performance.pdf",
        )
