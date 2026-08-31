from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import decode_cursor, encode_cursor
from app.repositories.transaction import TransactionRepository
from app.schemas.base import PaginatedResponse
from app.schemas.transaction import TransactionRead


class TransactionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = TransactionRepository(session)

    async def get_by_id(self, transaction_id: UUID) -> TransactionRead:
        txn = await self.repo.get_detail(transaction_id)
        if txn is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        return TransactionRead.model_validate(txn)

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
        limit: int = 25,
        cursor: str | None = None,
    ) -> PaginatedResponse[TransactionRead]:
        offset = decode_cursor(cursor) if cursor else 0
        rows = await self.repo.search(
            account_id=account_id,
            from_date=from_date,
            to_date=to_date,
            min_amount=min_amount,
            max_amount=max_amount,
            status=status,
            channel=channel,
            limit=limit,
            offset=offset,
        )
        has_more = len(rows) > limit
        items = rows[:limit]
        return PaginatedResponse(
            items=[TransactionRead.model_validate(t) for t in items],
            next_cursor=encode_cursor(offset + limit) if has_more else None,
            limit=limit,
        )
