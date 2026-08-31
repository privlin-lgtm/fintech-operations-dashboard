from uuid import UUID

from sqlalchemy import select

from app.models.account import Account
from app.repositories.base import BaseRepository


class AccountRepository(BaseRepository[Account]):
    model = Account

    async def list_by_customer(self, customer_id: UUID) -> list[Account]:
        stmt = (
            select(Account)
            .where(Account.customer_id == customer_id, Account.deleted_at.is_(None))
            .order_by(Account.opened_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
