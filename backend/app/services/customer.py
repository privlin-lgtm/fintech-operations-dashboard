from enum import Enum
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError
from app.core.pagination import decode_cursor, paginate
from app.core.sorting import decode_sort_cursor, paginate_sorted
from app.models.account import Account
from app.models.alert import Alert
from app.models.case import Case
from app.models.customer import Customer
from app.models.user import User
from app.repositories.account import AccountRepository
from app.repositories.alert import AlertRepository
from app.repositories.audit_log import AuditLogRepository
from app.repositories.case import CaseRepository
from app.repositories.customer import CUSTOMER_SORT_COLUMNS, CustomerRepository, parse_customer_sort
from app.schemas.account import AccountRead
from app.schemas.alert import AlertRead
from app.schemas.base import PaginatedResponse
from app.schemas.case import CaseRead
from app.schemas.customer import (
    CustomerCreate,
    CustomerProfile,
    CustomerRead,
    CustomerUpdate,
)
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
        self,
        *,
        query: str | None = None,
        status: str | None = None,
        risk_tier: str | None = None,
        kyc_status: str | None = None,
        sort: str = "-created_at",
        limit: int = 25,
        cursor: str | None = None,
    ) -> PaginatedResponse[CustomerRead]:
        sort_spec = parse_customer_sort(sort)
        parsed_cursor = (
            decode_sort_cursor(cursor, expected_sort=sort_spec.raw) if cursor else None
        )
        rows = await self.customer_repo.search(
            query=query,
            status=status,
            risk_tier=risk_tier,
            kyc_status=kyc_status,
            sort=sort_spec,
            limit=limit,
            cursor=parsed_cursor,
        )
        column = CUSTOMER_SORT_COLUMNS[sort_spec.field]
        items, next_cursor = paginate_sorted(
            rows,
            limit,
            sort=sort_spec.raw,
            get_sort_value=lambda row: getattr(row, column.key),
        )
        return PaginatedResponse(
            items=[CustomerRead.model_validate(c) for c in items],
            next_cursor=next_cursor,
            limit=limit,
        )

    async def create(self, data: CustomerCreate, *, actor: User) -> CustomerRead:
        if data.email:
            existing = await self.customer_repo.get_by_email(str(data.email))
            if existing is not None:
                raise ConflictError("A customer with that email already exists")

        customer = Customer(
            full_name=data.full_name,
            email=str(data.email) if data.email else None,
            phone=data.phone,
            kyc_status=data.kyc_status.value,
            risk_tier=data.risk_tier.value,
            status=data.status.value,
        )
        try:
            created = await self.customer_repo.add(customer)
        except IntegrityError as exc:
            # The pre-check above is a fast, friendly path — this is the real
            # guard, since two concurrent creates can both pass that check
            # before either commits (ux_customers_email_active is the backstop).
            raise ConflictError("A customer with that email already exists") from exc

        await self.audit_repo.record(
            actor_id=actor.id,
            action="create",
            resource_type="customer",
            resource_id=created.id,
        )
        return CustomerRead.model_validate(created)

    async def update(
        self, customer_id: UUID, data: CustomerUpdate, *, actor: User
    ) -> CustomerRead:
        customer = await self._get_or_404(customer_id)
        payload = data.model_dump(exclude_unset=True)

        if "email" in payload:
            email = payload.pop("email")
            if email is not None:
                email = str(email)
                existing = await self.customer_repo.get_by_email(email)
                if existing is not None and existing.id != customer.id:
                    raise ConflictError("A customer with that email already exists")
            customer.email = email

        for field, value in payload.items():
            setattr(customer, field, value.value if isinstance(value, Enum) else value)

        try:
            await self.customer_repo.session.flush()
        except IntegrityError as exc:
            raise ConflictError("A customer with that email already exists") from exc
        await self.customer_repo.session.refresh(customer)
        await self.audit_repo.record(
            actor_id=actor.id,
            action="update",
            resource_type="customer",
            resource_id=customer.id,
            metadata={"fields": sorted(data.model_dump(exclude_unset=True).keys())},
        )
        return CustomerRead.model_validate(customer)

    async def delete(self, customer_id: UUID, *, actor: User) -> None:
        customer = await self._get_or_404(customer_id)

        open_cases = await self.case_repo.count(
            Case.customer_id == customer_id, Case.status.not_like("closed%")
        )
        if open_cases:
            raise ConflictError(
                f"Cannot delete customer with {open_cases} open case(s) — close them first"
            )

        await self.customer_repo.soft_delete(customer)
        await self.audit_repo.record(
            actor_id=actor.id,
            action="delete",
            resource_type="customer",
            resource_id=customer_id,
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

    async def _get_or_404(self, customer_id: UUID) -> Customer:
        customer = await self.customer_repo.get_active_by_id(customer_id)
        if customer is None:
            raise NotFoundError("customer", customer_id)
        return customer

    async def _ensure_exists_if_empty(self, customer_id: UUID, rows: list) -> None:
        if not rows and await self.customer_repo.get_active_by_id(customer_id) is None:
            raise NotFoundError("customer", customer_id)
