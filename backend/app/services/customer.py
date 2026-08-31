from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import decode_cursor, encode_cursor
from app.repositories.account import AccountRepository
from app.repositories.alert import AlertRepository
from app.repositories.case import CaseRepository
from app.repositories.customer import CustomerRepository
from app.schemas.account import AccountRead
from app.schemas.alert import AlertRead
from app.schemas.base import PaginatedResponse
from app.schemas.case import CaseRead
from app.schemas.customer import CustomerProfile, CustomerRead


class CustomerService:
    def __init__(self, session: AsyncSession) -> None:
        self.customer_repo = CustomerRepository(session)
        self.account_repo = AccountRepository(session)
        self.case_repo = CaseRepository(session)
        self.alert_repo = AlertRepository(session)

    async def search(
        self,
        *,
        query: str | None,
        limit: int = 25,
        cursor: str | None = None,
    ) -> PaginatedResponse[CustomerRead]:
        offset = decode_cursor(cursor) if cursor else 0
        rows = await self.customer_repo.search(query=query, limit=limit, offset=offset)
        has_more = len(rows) > limit
        items = rows[:limit]
        return PaginatedResponse(
            items=[CustomerRead.model_validate(c) for c in items],
            next_cursor=encode_cursor(offset + limit) if has_more else None,
            limit=limit,
        )

    async def get_profile(self, customer_id: UUID) -> CustomerProfile:
        customer = await self.customer_repo.get_profile(customer_id)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return CustomerProfile.model_validate(customer)

    async def list_accounts(self, customer_id: UUID) -> list[AccountRead]:
        await self._ensure_exists(customer_id)
        accounts = await self.account_repo.list_by_customer(customer_id)
        return [AccountRead.model_validate(a) for a in accounts]

    async def list_cases(self, customer_id: UUID) -> list[CaseRead]:
        await self._ensure_exists(customer_id)
        cases = await self.case_repo.list_by_customer(customer_id)
        return [CaseRead.model_validate(c) for c in cases]

    async def list_alerts(self, customer_id: UUID) -> list[AlertRead]:
        await self._ensure_exists(customer_id)
        alerts = await self.alert_repo.list_by_customer(customer_id)
        return [AlertRead.model_validate(a) for a in alerts]

    async def _ensure_exists(self, customer_id: UUID) -> None:
        customer = await self.customer_repo.get_active_by_id(customer_id)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
