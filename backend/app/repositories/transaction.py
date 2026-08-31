import re
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Text, and_, exists, func, or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import ColumnElement

from app.core.alert_permissions import OPEN_ALERT_STATUSES
from app.core.sorting import SortCursor, SortSpec, parse_sort
from app.models.account import Account
from app.models.alert import Alert
from app.models.case import Case, CaseTransactionLink
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository

_LIKE_ESCAPE_RE = re.compile(r"([%_\\])")

TRANSACTION_SORT_COLUMNS: dict[str, Any] = {
    "created_at": Transaction.created_at,
    "amount_cents": Transaction.amount_cents,
    "status": Transaction.status,
    "risk_score": Transaction.risk_score,
}


def _escape_like(value: str) -> str:
    return _LIKE_ESCAPE_RE.sub(r"\\\1", value)


def parse_transaction_sort(raw: str) -> SortSpec:
    return parse_sort(raw, allowed=set(TRANSACTION_SORT_COLUMNS))


class TransactionRepository(BaseRepository[Transaction]):
    model = Transaction

    async def get_detail(self, transaction_id: UUID) -> Transaction | None:
        stmt = (
            self._base_query()
            .options(
                selectinload(Transaction.account),
                selectinload(Transaction.alerts),
                selectinload(Transaction.case_links).selectinload(CaseTransactionLink.case),
            )
            .where(Transaction.id == transaction_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        *,
        query: str | None = None,
        customer_id: UUID | None = None,
        account_id: UUID | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        min_amount: int | None = None,
        max_amount: int | None = None,
        status: str | None = None,
        channel: str | None = None,
        direction: str | None = None,
        sort: SortSpec,
        limit: int,
        cursor: SortCursor | None,
    ) -> list[Transaction]:
        stmt = self._base_query()
        if customer_id:
            stmt = stmt.join(Account, Transaction.account_id == Account.id)
        stmt = self._apply_filters(
            stmt,
            query=query,
            customer_id=customer_id,
            account_id=account_id,
            from_date=from_date,
            to_date=to_date,
            min_amount=min_amount,
            max_amount=max_amount,
            status=status,
            channel=channel,
            direction=direction,
        )
        stmt = self._apply_sort_page(stmt, sort=sort, cursor=cursor, limit=limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def has_open_alert(self, transaction_id: UUID) -> bool:
        result = await self.session.execute(
            select(
                exists().where(
                    Alert.transaction_id == transaction_id,
                    Alert.deleted_at.is_(None),
                    Alert.status.in_(OPEN_ALERT_STATUSES),
                )
            )
        )
        return result.scalar_one()

    async def has_open_case(self, transaction_id: UUID) -> bool:
        result = await self.session.execute(
            select(
                exists(
                    select(1)
                    .select_from(CaseTransactionLink)
                    .join(Case, CaseTransactionLink.case_id == Case.id)
                    .where(
                        CaseTransactionLink.transaction_id == transaction_id,
                        Case.deleted_at.is_(None),
                        Case.status.not_like("closed%"),
                    )
                )
            )
        )
        return result.scalar_one()

    async def count_open_alerts(self, transaction_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Alert)
            .where(
                Alert.transaction_id == transaction_id,
                Alert.deleted_at.is_(None),
                Alert.status.in_(OPEN_ALERT_STATUSES),
            )
        )
        return result.scalar_one()

    async def count_open_cases(self, transaction_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(CaseTransactionLink)
            .join(Case, CaseTransactionLink.case_id == Case.id)
            .where(
                CaseTransactionLink.transaction_id == transaction_id,
                Case.deleted_at.is_(None),
                Case.status.not_like("closed%"),
            )
        )
        return result.scalar_one()

    def _apply_filters(
        self,
        stmt,
        *,
        query: str | None,
        customer_id: UUID | None,
        account_id: UUID | None,
        from_date: datetime | None,
        to_date: datetime | None,
        min_amount: int | None,
        max_amount: int | None,
        status: str | None,
        channel: str | None,
        direction: str | None,
    ):
        if query:
            pattern = f"%{_escape_like(query)}%"
            stmt = stmt.where(
                or_(
                    func.cast(Transaction.id, Text).ilike(pattern, escape="\\"),
                    Transaction.counterparty_masked.ilike(pattern, escape="\\"),
                )
            )
        if customer_id:
            stmt = stmt.where(Account.customer_id == customer_id)
        if account_id:
            stmt = stmt.where(Transaction.account_id == account_id)
        if from_date:
            stmt = stmt.where(Transaction.created_at >= from_date)
        if to_date:
            stmt = stmt.where(Transaction.created_at <= to_date)
        if min_amount is not None:
            stmt = stmt.where(Transaction.amount_cents >= min_amount)
        if max_amount is not None:
            stmt = stmt.where(Transaction.amount_cents <= max_amount)
        if status:
            stmt = stmt.where(Transaction.status == status)
        if channel:
            stmt = stmt.where(Transaction.channel == channel)
        if direction:
            stmt = stmt.where(Transaction.direction == direction)
        return stmt

    def _apply_sort_page(
        self,
        stmt,
        *,
        sort: SortSpec,
        cursor: SortCursor | None,
        limit: int,
    ):
        column = TRANSACTION_SORT_COLUMNS[sort.field]
        primary = column.desc().nullslast() if sort.descending else column.asc().nullsfirst()
        tiebreak = Transaction.id.desc() if sort.descending else Transaction.id.asc()
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
                and_(column == cursor_value, Transaction.id < cursor_id),
            )
        return or_(
            column > cursor_value,
            and_(column == cursor_value, Transaction.id > cursor_id),
        )

    @staticmethod
    def _coerce_cursor_value(field: str, raw: str) -> Any:
        if field == "created_at":
            return datetime.fromisoformat(raw)
        if field == "amount_cents":
            return int(raw)
        if field == "risk_score":
            return Decimal(raw) if raw != "None" else None
        return raw
