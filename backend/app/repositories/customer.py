import re
from uuid import UUID

from sqlalchemy import Text, func, or_

from app.core.pagination import Cursor
from app.models.customer import Customer
from app.repositories.base import BaseRepository

_LIKE_ESCAPE_RE = re.compile(r"([%_\\])")


def _escape_like(value: str) -> str:
    """Escape literal % / _ / \\ so user search text can't smuggle SQL wildcards."""
    return _LIKE_ESCAPE_RE.sub(r"\\\1", value)


class CustomerRepository(BaseRepository[Customer]):
    model = Customer

    async def get_active_by_id(self, customer_id: UUID) -> Customer | None:
        result = await self.session.execute(self._base_query().where(Customer.id == customer_id))
        return result.scalar_one_or_none()

    async def search(
        self,
        *,
        query: str | None,
        limit: int,
        cursor: Cursor | None,
    ) -> list[Customer]:
        stmt = self._base_query()
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
        stmt = self._keyset_page(stmt, cursor=cursor, limit=limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
