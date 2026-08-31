import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Text, and_, func, or_
from sqlalchemy.sql import ColumnElement

from app.core.sorting import SortCursor, SortSpec, parse_sort
from app.models.customer import CUSTOMER_SORTABLE_FIELDS, Customer
from app.repositories.base import BaseRepository

_LIKE_ESCAPE_RE = re.compile(r"([%_\\])")

CUSTOMER_SORT_COLUMNS: dict[str, Any] = {
    field: getattr(Customer, field) for field in CUSTOMER_SORTABLE_FIELDS
}


def _escape_like(value: str) -> str:
    """Escape literal % / _ / \\ so user search text can't smuggle SQL wildcards."""
    return _LIKE_ESCAPE_RE.sub(r"\\\1", value)


def parse_customer_sort(raw: str) -> SortSpec:
    return parse_sort(raw, allowed=set(CUSTOMER_SORT_COLUMNS))


class CustomerRepository(BaseRepository[Customer]):
    model = Customer

    async def get_active_by_id(self, customer_id: UUID) -> Customer | None:
        result = await self.session.execute(self._base_query().where(Customer.id == customer_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Customer | None:
        result = await self.session.execute(
            self._base_query().where(Customer.email == email)
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        *,
        query: str | None = None,
        status: str | None = None,
        risk_tier: str | None = None,
        kyc_status: str | None = None,
        sort: SortSpec,
        limit: int,
        cursor: SortCursor | None,
    ) -> list[Customer]:
        stmt = self._base_query()
        stmt = self._apply_filters(
            stmt,
            query=query,
            status=status,
            risk_tier=risk_tier,
            kyc_status=kyc_status,
        )
        stmt = self._apply_sort_page(stmt, sort=sort, cursor=cursor, limit=limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete(self, customer: Customer) -> Customer:
        customer.deleted_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(customer)
        return customer

    def _apply_filters(
        self,
        stmt,
        *,
        query: str | None,
        status: str | None,
        risk_tier: str | None,
        kyc_status: str | None,
    ):
        if query:
            pattern = f"%{_escape_like(query)}%"
            stmt = stmt.where(
                or_(
                    Customer.full_name.ilike(pattern, escape="\\"),
                    Customer.email.ilike(pattern, escape="\\"),
                    Customer.phone.ilike(pattern, escape="\\"),
                    func.cast(Customer.id, Text).ilike(pattern, escape="\\"),
                )
            )
        if status:
            stmt = stmt.where(Customer.status == status)
        if risk_tier:
            stmt = stmt.where(Customer.risk_tier == risk_tier)
        if kyc_status:
            stmt = stmt.where(Customer.kyc_status == kyc_status)
        return stmt

    def _apply_sort_page(
        self,
        stmt,
        *,
        sort: SortSpec,
        cursor: SortCursor | None,
        limit: int,
    ):
        column = CUSTOMER_SORT_COLUMNS[sort.field]
        primary = column.desc() if sort.descending else column.asc()
        tiebreak = Customer.id.desc() if sort.descending else Customer.id.asc()
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
                and_(column == cursor_value, Customer.id < cursor_id),
            )
        return or_(
            column > cursor_value,
            and_(column == cursor_value, Customer.id > cursor_id),
        )

    @staticmethod
    def _coerce_cursor_value(field: str, raw: str) -> Any:
        if field in ("created_at", "updated_at"):
            return datetime.fromisoformat(raw)
        return raw
