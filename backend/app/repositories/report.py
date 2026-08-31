from datetime import UTC, datetime

from sqlalchemy import and_, func, select

from app.core.exceptions import ValidationConflictError
from app.models.alert import Alert
from app.models.case import Case
from app.models.report import Report
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository

CASE_GROUP_BY_COLUMNS: dict[str, object] = {
    "status": Case.status,
    "priority": Case.priority,
    "case_type": Case.case_type,
}

TRANSACTION_GROUP_BY_COLUMNS: dict[str, object] = {
    "status": Transaction.status,
    "channel": Transaction.channel,
    "direction": Transaction.direction,
}

ALERT_GROUP_BY_COLUMNS: dict[str, object] = {
    "status": Alert.status,
    "severity": Alert.severity,
    "alert_type": Alert.alert_type,
}

SLA_GROUP_BY_COLUMNS: dict[str, object] = {
    "priority": Case.priority,
    "case_type": Case.case_type,
}


def _format_group(value: object) -> str:
    if value is None:
        return "unknown"
    if hasattr(value, "isoformat"):
        return value.isoformat()  # type: ignore[union-attr]
    return str(value)


def _validate_group_by(group_by: str, allowed: dict[str, object]) -> None:
    if group_by != "day" and group_by not in allowed:
        raise ValidationConflictError(
            f"Invalid group_by {group_by!r}; allowed: day, {', '.join(sorted(allowed))}"
        )


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

    def _apply_created_at_filters(
        self,
        stmt,
        *,
        from_date: datetime | None,
        to_date: datetime | None,
        column,
    ):
        if from_date:
            stmt = stmt.where(column >= from_date)
        if to_date:
            stmt = stmt.where(column <= to_date)
        return stmt

    async def case_volume_by_group(
        self,
        *,
        from_date: datetime | None,
        to_date: datetime | None,
        group_by: str,
    ) -> list[dict]:
        _validate_group_by(group_by, CASE_GROUP_BY_COLUMNS)
        if group_by == "day":
            group_column = func.date_trunc("day", Case.created_at)
            stmt = (
                select(group_column, func.count())
                .where(Case.deleted_at.is_(None))
                .group_by(group_column)
                .order_by(group_column)
            )
        else:
            column = CASE_GROUP_BY_COLUMNS[group_by]
            stmt = (
                select(column, func.count())
                .where(Case.deleted_at.is_(None))
                .group_by(column)
            )
        stmt = self._apply_created_at_filters(
            stmt, from_date=from_date, to_date=to_date, column=Case.created_at
        )
        result = await self.session.execute(stmt)
        return [{"group": _format_group(row[0]), "count": row[1]} for row in result.all()]

    async def transaction_volume_by_group(
        self,
        *,
        from_date: datetime | None,
        to_date: datetime | None,
        group_by: str,
    ) -> list[dict]:
        _validate_group_by(group_by, TRANSACTION_GROUP_BY_COLUMNS)
        amount_sum = func.coalesce(func.sum(Transaction.amount_cents), 0)
        if group_by == "day":
            group_column = func.date_trunc("day", Transaction.created_at)
            stmt = (
                select(group_column, func.count(), amount_sum)
                .where(Transaction.deleted_at.is_(None))
                .group_by(group_column)
                .order_by(group_column)
            )
        else:
            column = TRANSACTION_GROUP_BY_COLUMNS[group_by]
            stmt = (
                select(column, func.count(), amount_sum)
                .where(Transaction.deleted_at.is_(None))
                .group_by(column)
            )
        stmt = self._apply_created_at_filters(
            stmt, from_date=from_date, to_date=to_date, column=Transaction.created_at
        )
        result = await self.session.execute(stmt)
        return [
            {
                "group": _format_group(row[0]),
                "count": row[1],
                "total_amount_cents": int(row[2]),
            }
            for row in result.all()
        ]

    async def alert_volume_by_group(
        self,
        *,
        from_date: datetime | None,
        to_date: datetime | None,
        group_by: str,
    ) -> list[dict]:
        _validate_group_by(group_by, ALERT_GROUP_BY_COLUMNS)
        if group_by == "day":
            group_column = func.date_trunc("day", Alert.created_at)
            stmt = (
                select(group_column, func.count())
                .where(Alert.deleted_at.is_(None))
                .group_by(group_column)
                .order_by(group_column)
            )
        else:
            column = ALERT_GROUP_BY_COLUMNS[group_by]
            stmt = (
                select(column, func.count())
                .where(Alert.deleted_at.is_(None))
                .group_by(column)
            )
        stmt = self._apply_created_at_filters(
            stmt, from_date=from_date, to_date=to_date, column=Alert.created_at
        )
        result = await self.session.execute(stmt)
        return [{"group": _format_group(row[0]), "count": row[1]} for row in result.all()]

    async def sla_performance(
        self,
        *,
        from_date: datetime | None,
        to_date: datetime | None,
        group_by: str,
    ) -> dict:
        if group_by not in SLA_GROUP_BY_COLUMNS:
            raise ValidationConflictError(
                f"Invalid group_by {group_by!r}; allowed: {', '.join(sorted(SLA_GROUP_BY_COLUMNS))}"
            )

        closed_filters = [
            Case.deleted_at.is_(None),
            Case.closed_at.is_not(None),
        ]
        if from_date:
            closed_filters.append(Case.closed_at >= from_date)
        if to_date:
            closed_filters.append(Case.closed_at <= to_date)

        met_condition = and_(
            Case.sla_due_at.is_not(None),
            Case.closed_at <= Case.sla_due_at,
        )
        missed_condition = and_(
            Case.sla_due_at.is_not(None),
            Case.closed_at > Case.sla_due_at,
        )

        summary_stmt = select(
            func.count().filter(*closed_filters),
            func.count().filter(*closed_filters, met_condition),
            func.count().filter(*closed_filters, missed_condition),
        )
        summary_result = await self.session.execute(summary_stmt)
        total_closed, met_sla, missed_sla = summary_result.one()

        now = datetime.now(UTC)
        at_risk_result = await self.session.execute(
            select(func.count()).select_from(Case).where(
                Case.deleted_at.is_(None),
                Case.sla_due_at.is_not(None),
                Case.sla_due_at <= now,
                Case.status.not_like("closed%"),
            )
        )
        currently_at_risk = at_risk_result.scalar_one()

        group_column = SLA_GROUP_BY_COLUMNS[group_by]
        breakdown_stmt = (
            select(
                group_column,
                func.count().filter(*closed_filters),
                func.count().filter(*closed_filters, met_condition),
                func.count().filter(*closed_filters, missed_condition),
            )
            .where(Case.deleted_at.is_(None))
            .group_by(group_column)
        )
        breakdown_result = await self.session.execute(breakdown_stmt)
        breakdown = [
            {
                "group": _format_group(row[0]),
                "closed": row[1],
                "met_sla": row[2],
                "missed_sla": row[3],
            }
            for row in breakdown_result.all()
        ]

        compliance_rate = None
        if met_sla + missed_sla > 0:
            compliance_rate = round(met_sla / (met_sla + missed_sla), 4)

        return {
            "total_closed": total_closed,
            "met_sla": met_sla,
            "missed_sla": missed_sla,
            "currently_at_risk": currently_at_risk,
            "compliance_rate": compliance_rate,
            "breakdown": breakdown,
        }
