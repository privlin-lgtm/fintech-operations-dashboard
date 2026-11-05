from datetime import UTC, datetime
from uuid import UUID

from app.core.alert_permissions import (
    enforce_assign,
    enforce_delete,
    enforce_escalate,
    enforce_modify,
    enforce_resolve,
    enforce_view,
    is_terminal,
    validate_transition,
)
from app.core.exceptions import ConflictError, NotFoundError, ValidationConflictError
from app.core.pagination import Cursor
from app.core.sorting import decode_sort_cursor, paginate_sorted
from app.models.alert import Alert
from app.models.case import Case, CaseNote
from app.models.enums import AlertStatus
from app.models.user import User
from app.repositories.alert import ALERT_SORT_COLUMNS, AlertRepository, parse_alert_sort
from app.repositories.audit_log import AuditLogRepository
from app.repositories.case import CaseRepository
from app.repositories.customer import CustomerRepository
from app.repositories.user import UserRepository
from app.schemas.alert import (
    AlertAssign,
    AlertCreate,
    AlertDetail,
    AlertEscalate,
    AlertRead,
    AlertResolve,
    AlertUpdate,
)
from app.schemas.base import PaginatedResponse


class AlertService:
    def __init__(
        self,
        alert_repo: AlertRepository,
        case_repo: CaseRepository,
        audit_repo: AuditLogRepository,
        customer_repo: CustomerRepository,
        user_repo: UserRepository,
    ) -> None:
        self.repo = alert_repo
        self.case_repo = case_repo
        self.audit_repo = audit_repo
        self.customer_repo = customer_repo
        self.user_repo = user_repo

    async def create(self, data: AlertCreate, actor: User) -> AlertRead:
        customer = await self.customer_repo.get_active_by_id(data.customer_id)
        if customer is None:
            raise NotFoundError("customer", data.customer_id)

        status = AlertStatus.NEW.value
        assignee_id = data.assignee_id
        if assignee_id:
            await self._ensure_active_user(assignee_id)
            status = AlertStatus.ASSIGNED.value

        alert = Alert(
            customer_id=data.customer_id,
            transaction_id=data.transaction_id,
            alert_type=data.alert_type.value,
            severity=data.severity.value,
            status=status,
            triggering_reason=data.triggering_reason,
            assignee_id=assignee_id,
        )
        created = await self.repo.add(alert)
        await self._audit(actor, "create", created.id)
        return AlertRead.model_validate(created)

    async def get_by_id(self, alert_id: UUID, *, viewer: User) -> AlertDetail:
        alert = await self._get_or_404(alert_id)
        enforce_view(viewer, alert)
        await self._audit(viewer, "view", alert.id)
        detail = AlertDetail.model_validate(alert)
        if alert.assignee_id is not None:
            assignee = await self.user_repo.get_by_id(alert.assignee_id)
            detail.assignee_name = assignee.full_name if assignee else None
        return detail

    async def update(self, alert_id: UUID, data: AlertUpdate, actor: User) -> AlertRead:
        alert = await self._get_or_404(alert_id)
        enforce_modify(actor, alert)

        if data.severity:
            alert.severity = data.severity.value
        if data.triggering_reason:
            alert.triggering_reason = data.triggering_reason

        await self.repo.session.flush()
        await self.repo.session.refresh(alert)
        await self._audit(
            actor,
            "update",
            alert.id,
            metadata=data.model_dump(exclude_unset=True, mode="json"),
        )
        return AlertRead.model_validate(alert)

    async def delete(self, alert_id: UUID, actor: User) -> None:
        enforce_delete(actor)
        alert = await self._get_or_404(alert_id)
        await self.repo.soft_delete(alert)
        await self._audit(actor, "delete", alert.id)

    async def list_alerts(
        self,
        *,
        actor: User,
        query: str | None = None,
        customer_id: UUID | None = None,
        assignee_id: UUID | None = None,
        severity: str | None = None,
        status: str | None = None,
        alert_type: str | None = None,
        sort: str = "-created_at",
        limit: int = 25,
        cursor: str | None = None,
    ) -> PaginatedResponse[AlertRead]:
        sort_spec = parse_alert_sort(sort)
        parsed_cursor = (
            decode_sort_cursor(cursor, expected_sort=sort_spec.raw) if cursor else None
        )
        open_queue_for = actor.id if actor.role.name == "analyst" else None
        if actor.role.name == "analyst":
            assignee_id = None

        rows = await self.repo.search(
            query=query,
            customer_id=customer_id,
            assignee_id=assignee_id,
            open_queue_for=open_queue_for,
            severity=severity,
            status=status,
            alert_type=alert_type,
            sort=sort_spec,
            limit=limit,
            cursor=parsed_cursor,
        )
        column = ALERT_SORT_COLUMNS[sort_spec.field]
        page_rows, next_cursor = paginate_sorted(
            rows,
            limit,
            sort=sort_spec.raw,
            get_sort_value=lambda row: getattr(row, column.key),
        )
        return PaginatedResponse(
            items=[AlertRead.model_validate(a) for a in page_rows],
            next_cursor=next_cursor,
            limit=limit,
        )

    async def list_for_customer(
        self, customer_id: UUID, *, cursor: Cursor | None = None, limit: int = 25
    ) -> list[Alert]:
        return await self.repo.list_by_customer(customer_id, cursor=cursor, limit=limit)

    async def assign(self, alert_id: UUID, data: AlertAssign, actor: User) -> AlertRead:
        alert = await self._get_or_404(alert_id)
        enforce_assign(actor, alert)
        await self._ensure_active_user(data.assignee_id)

        validate_transition(alert.status, AlertStatus.ASSIGNED.value)
        alert.status = AlertStatus.ASSIGNED.value
        alert.assignee_id = data.assignee_id

        await self.repo.session.flush()
        await self.repo.session.refresh(alert)
        await self._audit(
            actor,
            "assign",
            alert.id,
            metadata={"assignee_id": str(data.assignee_id)},
        )
        return AlertRead.model_validate(alert)

    async def escalate(self, alert_id: UUID, data: AlertEscalate, actor: User) -> AlertRead:
        alert = await self._get_or_404(alert_id)
        enforce_escalate(actor, alert)

        case_id = data.case_id
        if case_id is None and data.create_case:
            case_number = await self.case_repo.next_case_number()
            case = Case(
                case_number=case_number,
                customer_id=alert.customer_id,
                owner_id=actor.id,
                case_type=data.case_type.value,
                priority=data.priority.value,
                status="new",
            )
            created = await self.case_repo.add(case)
            await self.case_repo.add_note(
                CaseNote(
                    case_id=created.id,
                    author_id=actor.id,
                    body=f"Case auto-created from alert {alert.id}",
                    is_system=True,
                )
            )
            case_id = created.id
        elif case_id is None:
            raise ValidationConflictError("Provide case_id or set create_case=true")

        validate_transition(alert.status, AlertStatus.ESCALATED.value)
        alert.status = AlertStatus.ESCALATED.value
        alert.case_id = case_id
        await self.repo.session.flush()
        await self.repo.session.refresh(alert)
        await self._audit(
            actor,
            "escalate",
            alert.id,
            metadata={"case_id": str(case_id)},
        )
        return AlertRead.model_validate(alert)

    async def resolve(self, alert_id: UUID, data: AlertResolve, actor: User) -> AlertRead:
        alert = await self._get_or_404(alert_id)
        if is_terminal(alert):
            raise ConflictError("Alert already resolved")
        enforce_resolve(actor, alert)

        validate_transition(alert.status, AlertStatus.RESOLVED.value)
        alert.status = AlertStatus.RESOLVED.value
        alert.dismissal_reason = data.reason
        alert.resolved_at = datetime.now(UTC)
        await self.repo.session.flush()
        await self.repo.session.refresh(alert)
        await self._audit(
            actor,
            "resolve",
            alert.id,
            metadata={"reason": data.reason},
        )
        return AlertRead.model_validate(alert)

    async def _ensure_active_user(self, user_id: UUID) -> None:
        user = await self.user_repo.get_active_by_id(user_id)
        if user is None:
            raise NotFoundError("user", user_id)

    async def _get_or_404(self, alert_id: UUID) -> Alert:
        alert = await self.repo.get_active_by_id(alert_id)
        if alert is None:
            raise NotFoundError("alert", alert_id)
        return alert

    async def _audit(
        self,
        actor: User,
        action: str,
        alert_id: UUID,
        *,
        metadata: dict | None = None,
    ) -> None:
        await self.audit_repo.record(
            actor_id=actor.id,
            action=action,
            resource_type="alert",
            resource_id=alert_id,
            metadata=metadata or {},
        )
