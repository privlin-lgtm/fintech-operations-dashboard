from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, get_customer_service
from app.models.user import User
from app.schemas.account import AccountRead
from app.schemas.alert import AlertRead
from app.schemas.base import PaginatedResponse
from app.schemas.case import CaseRead
from app.schemas.customer import CustomerProfile, CustomerRead
from app.services.customer import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=PaginatedResponse[CustomerRead])
async def search_customers(
    q: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=200),
    cursor: str | None = Query(default=None),
    _user: User = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> PaginatedResponse[CustomerRead]:
    return await service.search(query=q, limit=limit, cursor=cursor)


@router.get("/{customer_id}", response_model=CustomerProfile)
async def get_customer(
    customer_id: UUID,
    _user: User = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerProfile:
    return await service.get_profile(customer_id)


@router.get("/{customer_id}/accounts", response_model=list[AccountRead])
async def list_customer_accounts(
    customer_id: UUID,
    _user: User = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> list[AccountRead]:
    return await service.list_accounts(customer_id)


@router.get("/{customer_id}/cases", response_model=list[CaseRead])
async def list_customer_cases(
    customer_id: UUID,
    _user: User = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> list[CaseRead]:
    return await service.list_cases(customer_id)


@router.get("/{customer_id}/alerts", response_model=list[AlertRead])
async def list_customer_alerts(
    customer_id: UUID,
    _user: User = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> list[AlertRead]:
    return await service.list_alerts(customer_id)
