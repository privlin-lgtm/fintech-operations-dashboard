from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, get_transaction_service
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.transaction import TransactionRead
from app.services.transaction import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/{transaction_id}", response_model=TransactionRead)
async def get_transaction(
    transaction_id: UUID,
    _user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionRead:
    return await service.get_by_id(transaction_id)


@router.get("", response_model=PaginatedResponse[TransactionRead])
async def search_transactions(
    account_id: UUID | None = Query(default=None),
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    min_amount: int | None = Query(default=None),
    max_amount: int | None = Query(default=None),
    status: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=200),
    cursor: str | None = Query(default=None),
    _user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
) -> PaginatedResponse[TransactionRead]:
    return await service.search(
        account_id=account_id,
        from_date=from_date,
        to_date=to_date,
        min_amount=min_amount,
        max_amount=max_amount,
        status=status,
        channel=channel,
        limit=limit,
        cursor=cursor,
    )
