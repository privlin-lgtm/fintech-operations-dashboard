from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report
from app.models.user import User
from app.repositories.alert import AlertRepository
from app.repositories.report import ReportRepository
from app.schemas.report import DashboardSummary, ReportRead, ReportScheduleCreate


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ReportRepository(session)
        self.alert_repo = AlertRepository(session)

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
        return ReportRead.model_validate(created)
