from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.transaction import Transaction
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    model = Transaction

    def _active(self):
        return select(Transaction).where(Transaction.deleted_at.is_(None))

    async def get_detail(self, transaction_id: UUID) -> Transaction | None:
        stmt = (
            self._active()
            .options(selectinload(Transaction.account))
            .where(Transaction.id == transaction_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        *,
        account_id: UUID | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        min_amount: int | None = None,
        max_amount: int | None = None,
        status: str | None = None,
        channel: str | None = None,
        limit: int,
        offset: int,
    ) -> list[Transaction]:
        stmt = self._active().order_by(Transaction.created_at.desc())
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
        result = await self.session.execute(stmt.limit(limit + 1).offset(offset))
        return list(result.scalars().all())
