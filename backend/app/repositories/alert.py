import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Text, and_, func, or_, select
from sqlalchemy.sql import ColumnElement

from app.core.sorting import SortCursor, SortSpec, parse_sort
from app.models.alert import Alert
from app.repositories.base import BaseRepository

_LIKE_ESCAPE_RE = re.compile(r"([%_\\])")

ALERT_SORT_COLUMNS: dict[str, Any] = {
    "created_at": Alert.created_at,
    "severity": Alert.severity,
    "status": Alert.status,
}


def _escape_like(value: str) -> str:
    return _LIKE_ESCAPE_RE.sub(r"\\\1", value)


def parse_alert_sort(raw: str) -> SortSpec:
    return parse_sort(raw, allowed=set(ALERT_SORT_COLUMNS))


class AlertRepository(BaseRepository[Alert]):
    model = Alert

    async def get_active_by_id(self, alert_id: UUID) -> Alert | None:
        result = await self.session.execute(self._base_query().where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def list_by_customer(
        self, customer_id: UUID, *, cursor=None, limit: int = 25
    ) -> list[Alert]:
        stmt = self._base_query().where(Alert.customer_id == customer_id)
        stmt = self._keyset_page(stmt, cursor=cursor, limit=limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_recent_by_customer(self, customer_id: UUID, *, limit: int = 5) -> list[Alert]:
        stmt = (
            self._base_query()
            .where(Alert.customer_id == customer_id)
            .order_by(Alert.created_at.desc(), Alert.id.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self,
        *,
        query: str | None = None,
        customer_id: UUID | None = None,
        assignee_id: UUID | None = None,
        open_queue_for: UUID | None = None,
        severity: str | None = None,
        status: str | None = None,
        alert_type: str | None = None,
        sort: SortSpec,
        limit: int,
        cursor: SortCursor | None = None,
    ) -> list[Alert]:
        stmt = self._base_query()
        stmt = self._apply_filters(
            stmt,
            query=query,
            customer_id=customer_id,
            assignee_id=assignee_id,
            open_queue_for=open_queue_for,
            severity=severity,
            status=status,
            alert_type=alert_type,
        )
        stmt = self._apply_sort_page(stmt, sort=sort, cursor=cursor, limit=limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_status(self, status: str) -> int:
        return await self.count(Alert.status == status)

    async def soft_delete(self, alert: Alert) -> Alert:
        alert.deleted_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(alert)
        return alert

    def _apply_filters(
        self,
        stmt,
        *,
        query: str | None,
        customer_id: UUID | None,
        assignee_id: UUID | None,
        open_queue_for: UUID | None,
        severity: str | None,
        status: str | None,
        alert_type: str | None,
    ):
        if query:
            pattern = f"%{_escape_like(query)}%"
            stmt = stmt.where(
                or_(
                    func.cast(Alert.id, Text).ilike(pattern, escape="\\"),
                    Alert.triggering_reason.ilike(pattern, escape="\\"),
                )
            )
        if customer_id:
            stmt = stmt.where(Alert.customer_id == customer_id)
        if assignee_id:
            stmt = stmt.where(Alert.assignee_id == assignee_id)
        if open_queue_for is not None:
            stmt = stmt.where(
                or_(
                    Alert.assignee_id == open_queue_for,
                    Alert.status == "new",
                )
            )
        if severity:
            stmt = stmt.where(Alert.severity == severity)
        if status:
            stmt = stmt.where(Alert.status == status)
        if alert_type:
            stmt = stmt.where(Alert.alert_type == alert_type)
        return stmt

    def _apply_sort_page(
        self,
        stmt,
        *,
        sort: SortSpec,
        cursor: SortCursor | None,
        limit: int,
    ):
        column = ALERT_SORT_COLUMNS[sort.field]
        primary = column.desc() if sort.descending else column.asc()
        tiebreak = Alert.id.desc() if sort.descending else Alert.id.asc()
        stmt = stmt.order_by(primary, tiebreak)

        if cursor is not None:
            cursor_value = self._coerce_cursor_value(sort.field, cursor.sort_value)
            stmt = stmt.where(self._keyset_clause(column, cursor_value, cursor.id, sort.descending))

        return stmt.limit(limit + 1)

    def _keyset_clause(
        self,
        column: ColumnElement,
        cursor_value: Any,
        cursor_id: UUID,
        descending: bool,
    ):
        if descending:
            return or_(
                column < cursor_value,
                and_(column == cursor_value, Alert.id < cursor_id),
            )
        return or_(
            column > cursor_value,
            and_(column == cursor_value, Alert.id > cursor_id),
        )

    @staticmethod
    def _coerce_cursor_value(field: str, raw: str) -> Any:
        if field == "created_at":
            return datetime.fromisoformat(raw)
        return raw
