from uuid import UUID

from app.core.pagination import Cursor
from app.models.account import Account
from app.repositories.base import BaseRepository


class AccountRepository(BaseRepository[Account]):
    model = Account

    async def list_by_customer(
        self, customer_id: UUID, *, cursor: Cursor | None = None, limit: int = 25
    ) -> list[Account]:
        stmt = self._base_query().where(Account.customer_id == customer_id)
        stmt = self._keyset_page(stmt, cursor=cursor, limit=limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_recent_by_customer(self, customer_id: UUID, *, limit: int = 5) -> list[Account]:
        stmt = (
            self._base_query()
            .where(Account.customer_id == customer_id)
            .order_by(Account.created_at.desc(), Account.id.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
