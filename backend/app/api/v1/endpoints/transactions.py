from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUserDep, TransactionServiceDep
from app.schemas.base import PaginatedResponse
from app.schemas.transaction import TransactionRead

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/{transaction_id}", response_model=TransactionRead)
async def get_transaction(
    transaction_id: UUID, _user: CurrentUserDep, service: TransactionServiceDep
) -> TransactionRead:
    return await service.get_by_id(transaction_id)


@router.get("", response_model=PaginatedResponse[TransactionRead])
async def search_transactions(
    _user: CurrentUserDep,
    service: TransactionServiceDep,
    account_id: Annotated[UUID | None, Query()] = None,
    from_date: Annotated[datetime | None, Query(alias="from")] = None,
    to_date: Annotated[datetime | None, Query(alias="to")] = None,
    min_amount: Annotated[int | None, Query()] = None,
    max_amount: Annotated[int | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    channel: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 25,
    cursor: Annotated[str | None, Query()] = None,
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
