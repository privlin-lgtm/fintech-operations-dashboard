from datetime import datetime

from app.models.report import Report
from app.models.user import User
from app.repositories.alert import AlertRepository
from app.repositories.audit_log import AuditLogRepository
from app.repositories.report import ReportRepository
from app.schemas.report import DashboardSummary, ReportRead, ReportScheduleCreate


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

    async def case_report(
        self,
        *,
        from_date: datetime | None,
        to_date: datetime | None,
        group_by: str,
    ) -> list[dict]:
        return await self.repo.case_volume_by_group(
            from_date=from_date, to_date=to_date, group_by=group_by
        )

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
