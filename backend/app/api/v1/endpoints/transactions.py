from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import TransactionServiceDep, require_roles
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.transaction import TransactionDetail, TransactionRead, TransactionSearchParams

router = APIRouter(prefix="/transactions", tags=["transactions"])

TRANSACTION_READ_ROLES = (
    "analyst",
    "investigator",
    "team_lead",
    "compliance_auditor",
    "admin",
)
TransactionReaderDep = Annotated[User, Depends(require_roles(*TRANSACTION_READ_ROLES))]


@router.get("", response_model=PaginatedResponse[TransactionRead])
async def search_transactions(
    params: Annotated[TransactionSearchParams, Query()],
    _user: TransactionReaderDep,
    service: TransactionServiceDep,
) -> PaginatedResponse[TransactionRead]:
    return await service.search(
        query=params.q,
        customer_id=params.customer_id,
        account_id=params.account_id,
        from_date=params.from_date,
        to_date=params.to_date,
        min_amount=params.min_amount,
        max_amount=params.max_amount,
        status=params.status.value if params.status else None,
        channel=params.channel.value if params.channel else None,
        direction=params.direction.value if params.direction else None,
        sort=params.sort,
        limit=params.limit,
        cursor=params.cursor,
    )


@router.get("/{transaction_id}", response_model=TransactionDetail)
async def get_transaction(
    transaction_id: UUID,
    current_user: TransactionReaderDep,
    service: TransactionServiceDep,
) -> TransactionDetail:
    return await service.get_detail(transaction_id, viewer=current_user)
