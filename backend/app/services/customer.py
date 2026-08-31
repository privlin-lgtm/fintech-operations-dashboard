from uuid import UUID

from app.core.exceptions import NotFoundError
from app.core.pagination import decode_cursor, paginate
from app.models.account import Account
from app.models.alert import Alert
from app.models.case import Case
from app.models.user import User
from app.repositories.account import AccountRepository
from app.repositories.alert import AlertRepository
from app.repositories.audit_log import AuditLogRepository
from app.repositories.case import CaseRepository
from app.repositories.customer import CustomerRepository
from app.schemas.account import AccountRead
from app.schemas.alert import AlertRead
from app.schemas.base import PaginatedResponse
from app.schemas.case import CaseRead
from app.schemas.customer import CustomerProfile, CustomerRead
from app.services.alert import AlertService
from app.services.case import CaseService

RECENT_PREVIEW_LIMIT = 5
OPEN_ALERT_STATUSES = ("new", "under_review")


class CustomerService:
    def __init__(
        self,
        customer_repo: CustomerRepository,
        account_repo: AccountRepository,
        case_repo: CaseRepository,
        alert_repo: AlertRepository,
        audit_repo: AuditLogRepository,
        case_service: CaseService,
        alert_service: AlertService,
    ) -> None:
        self.customer_repo = customer_repo
        self.account_repo = account_repo
        self.case_repo = case_repo
        self.alert_repo = alert_repo
        self.audit_repo = audit_repo
        self.case_service = case_service
        self.alert_service = alert_service

    async def search(
        self, *, query: str | None, limit: int = 25, cursor: str | None = None
    ) -> PaginatedResponse[CustomerRead]:
        parsed_cursor = decode_cursor(cursor) if cursor else None
        rows = await self.customer_repo.search(query=query, limit=limit, cursor=parsed_cursor)
        items, next_cursor = paginate(rows, limit)
        return PaginatedResponse(
            items=[CustomerRead.model_validate(c) for c in items],
            next_cursor=next_cursor,
            limit=limit,
        )

    async def get_profile(self, customer_id: UUID, *, viewer: User) -> CustomerProfile:
        customer = await self.customer_repo.get_active_by_id(customer_id)
        if customer is None:
            raise NotFoundError("customer", customer_id)

        account_count = await self.account_repo.count(Account.customer_id == customer_id)
        open_case_count = await self.case_repo.count(
            Case.customer_id == customer_id, Case.status.not_like("closed%")
        )
        total_case_count = await self.case_repo.count(Case.customer_id == customer_id)
        open_alert_count = await self.alert_repo.count(
            Alert.customer_id == customer_id, Alert.status.in_(OPEN_ALERT_STATUSES)
        )
        recent_accounts = await self.account_repo.list_recent_by_customer(
            customer_id, limit=RECENT_PREVIEW_LIMIT
        )
        recent_cases = await self.case_repo.list_recent_by_customer(
            customer_id, limit=RECENT_PREVIEW_LIMIT
        )
        recent_alerts = await self.alert_repo.list_recent_by_customer(
            customer_id, limit=RECENT_PREVIEW_LIMIT
        )

        # FR-CS-5: every customer record view is logged — who, when, what.
        await self.audit_repo.record(
            actor_id=viewer.id,
            action="view",
            resource_type="customer",
            resource_id=customer_id,
        )

        return CustomerProfile(
            id=customer.id,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            full_name=customer.full_name,
            email=customer.email,
            phone=customer.phone,
            kyc_status=customer.kyc_status,
            risk_tier=customer.risk_tier,
            status=customer.status,
            account_count=account_count,
            open_case_count=open_case_count,
            total_case_count=total_case_count,
            open_alert_count=open_alert_count,
            recent_accounts=[AccountRead.model_validate(a) for a in recent_accounts],
            recent_cases=[CaseRead.model_validate(c) for c in recent_cases],
            recent_alerts=[AlertRead.model_validate(a) for a in recent_alerts],
        )

    async def list_accounts(
        self, customer_id: UUID, *, viewer: User, limit: int = 25, cursor: str | None = None
    ) -> PaginatedResponse[AccountRead]:
        parsed_cursor = decode_cursor(cursor) if cursor else None
        rows = await self.account_repo.list_by_customer(customer_id, cursor=parsed_cursor, limit=limit)
        await self._ensure_exists_if_empty(customer_id, rows)
        items, next_cursor = paginate(rows, limit)
        await self.audit_repo.record(
            actor_id=viewer.id, action="view", resource_type="customer_accounts", resource_id=customer_id
        )
        return PaginatedResponse(
            items=[AccountRead.model_validate(a) for a in items], next_cursor=next_cursor, limit=limit
        )

    async def list_cases(
        self, customer_id: UUID, *, viewer: User, limit: int = 25, cursor: str | None = None
    ) -> PaginatedResponse[CaseRead]:
        parsed_cursor = decode_cursor(cursor) if cursor else None
        rows = await self.case_service.list_for_customer(customer_id, cursor=parsed_cursor, limit=limit)
        await self._ensure_exists_if_empty(customer_id, rows)
        items, next_cursor = paginate(rows, limit)
        await self.audit_repo.record(
            actor_id=viewer.id, action="view", resource_type="customer_cases", resource_id=customer_id
        )
        return PaginatedResponse(
            items=[CaseRead.model_validate(c) for c in items], next_cursor=next_cursor, limit=limit
        )

    async def list_alerts(
        self, customer_id: UUID, *, viewer: User, limit: int = 25, cursor: str | None = None
    ) -> PaginatedResponse[AlertRead]:
        parsed_cursor = decode_cursor(cursor) if cursor else None
        rows = await self.alert_service.list_for_customer(customer_id, cursor=parsed_cursor, limit=limit)
        await self._ensure_exists_if_empty(customer_id, rows)
        items, next_cursor = paginate(rows, limit)
        await self.audit_repo.record(
            actor_id=viewer.id, action="view", resource_type="customer_alerts", resource_id=customer_id
        )
        return PaginatedResponse(
            items=[AlertRead.model_validate(a) for a in items], next_cursor=next_cursor, limit=limit
        )

    async def _ensure_exists_if_empty(self, customer_id: UUID, rows: list) -> None:
        """Only pay for the extra existence check when the list came back empty —
        distinguishes 'no customer' (404) from 'customer, no rows yet' (empty page)
        without a round trip on every request."""
        if not rows and await self.customer_repo.get_active_by_id(customer_id) is None:
            raise NotFoundError("customer", customer_id)
