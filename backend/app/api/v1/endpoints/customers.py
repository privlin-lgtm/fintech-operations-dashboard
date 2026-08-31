from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import CustomerServiceDep, require_roles
from app.models.user import User
from app.schemas.account import AccountRead
from app.schemas.alert import AlertRead
from app.schemas.base import PaginatedResponse
from app.schemas.case import CaseRead
from app.schemas.customer import (
    CustomerCreate,
    CustomerProfile,
    CustomerRead,
    CustomerSearchParams,
    CustomerUpdate,
)

router = APIRouter(prefix="/customers", tags=["customers"])

# Every role that touches customer PII at all (SEC-2).
CUSTOMER_READ_ROLES = ("analyst", "investigator", "team_lead", "compliance_auditor", "admin")
# Seed/admin writes — not front-line analysts (SEC-2 least privilege).
CUSTOMER_WRITE_ROLES = ("admin", "team_lead")

CustomerReaderDep = Annotated[User, Depends(require_roles(*CUSTOMER_READ_ROLES))]
CustomerWriterDep = Annotated[User, Depends(require_roles(*CUSTOMER_WRITE_ROLES))]


@router.get("", response_model=PaginatedResponse[CustomerRead])
async def search_customers(
    params: Annotated[CustomerSearchParams, Query()],
    _user: CustomerReaderDep,
    service: CustomerServiceDep,
) -> PaginatedResponse[CustomerRead]:
    return await service.search(
        query=params.q,
        status=params.status.value if params.status else None,
        risk_tier=params.risk_tier.value if params.risk_tier else None,
        kyc_status=params.kyc_status.value if params.kyc_status else None,
        sort=params.sort,
        limit=params.limit,
        cursor=params.cursor,
    )


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(
    data: CustomerCreate,
    current_user: CustomerWriterDep,
    service: CustomerServiceDep,
) -> CustomerRead:
    return await service.create(data, actor=current_user)


@router.get("/{customer_id}", response_model=CustomerProfile)
async def get_customer(
    customer_id: UUID,
    current_user: CustomerReaderDep,
    service: CustomerServiceDep,
) -> CustomerProfile:
    return await service.get_profile(customer_id, viewer=current_user)


@router.patch("/{customer_id}", response_model=CustomerRead)
async def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    current_user: CustomerWriterDep,
    service: CustomerServiceDep,
) -> CustomerRead:
    return await service.update(customer_id, data, actor=current_user)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    current_user: CustomerWriterDep,
    service: CustomerServiceDep,
) -> None:
    await service.delete(customer_id, actor=current_user)


@router.get("/{customer_id}/accounts", response_model=PaginatedResponse[AccountRead])
async def list_customer_accounts(
    customer_id: UUID,
    current_user: CustomerReaderDep,
    service: CustomerServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 25,
    cursor: Annotated[str | None, Query()] = None,
) -> PaginatedResponse[AccountRead]:
    return await service.list_accounts(customer_id, viewer=current_user, limit=limit, cursor=cursor)


@router.get("/{customer_id}/cases", response_model=PaginatedResponse[CaseRead])
async def list_customer_cases(
    customer_id: UUID,
    current_user: CustomerReaderDep,
    service: CustomerServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 25,
    cursor: Annotated[str | None, Query()] = None,
) -> PaginatedResponse[CaseRead]:
    return await service.list_cases(customer_id, viewer=current_user, limit=limit, cursor=cursor)


@router.get("/{customer_id}/alerts", response_model=PaginatedResponse[AlertRead])
async def list_customer_alerts(
    customer_id: UUID,
    current_user: CustomerReaderDep,
    service: CustomerServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 25,
    cursor: Annotated[str | None, Query()] = None,
) -> PaginatedResponse[AlertRead]:
    return await service.list_alerts(customer_id, viewer=current_user, limit=limit, cursor=cursor)
