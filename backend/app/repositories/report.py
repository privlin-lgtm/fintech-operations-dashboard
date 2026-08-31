from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select

from app.models.case import Case
from app.models.report import Report
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    model = Report

    async def add_schedule(self, report: Report) -> Report:
        return await self.add(report)

    async def count_open_cases(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Case).where(
                Case.deleted_at.is_(None),
                Case.status.not_like("closed%"),
            )
        )
        return result.scalar_one()

    async def count_sla_at_risk(self) -> int:
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(func.count()).select_from(Case).where(
                Case.deleted_at.is_(None),
                Case.sla_due_at.is_not(None),
                Case.sla_due_at <= now,
                Case.status.not_like("closed%"),
            )
        )
        return result.scalar_one()

    async def count_cases_closed_today(self) -> int:
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count()).select_from(Case).where(
                Case.deleted_at.is_(None),
                Case.closed_at.is_not(None),
                Case.closed_at >= today_start,
            )
        )
        return result.scalar_one()

    async def case_volume_by_group(
        self,
        *,
        from_date: datetime | None,
        to_date: datetime | None,
        group_by: str,
    ) -> list[dict]:
        column = getattr(Case, group_by, Case.status)
        stmt = (
            select(column, func.count())
            .where(Case.deleted_at.is_(None))
            .group_by(column)
        )
        if from_date:
            stmt = stmt.where(Case.created_at >= from_date)
        if to_date:
            stmt = stmt.where(Case.created_at <= to_date)
        result = await self.session.execute(stmt)
        return [{"group": row[0], "count": row[1]} for row in result.all()]
