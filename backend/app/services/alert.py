from datetime import UTC, datetime
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError, ValidationConflictError
from app.core.pagination import Cursor, decode_cursor, paginate
from app.models.alert import Alert
from app.models.case import Case, CaseNote
from app.models.user import User
from app.repositories.alert import AlertRepository
from app.repositories.audit_log import AuditLogRepository
from app.repositories.case import CaseRepository
from app.schemas.alert import AlertDismiss, AlertEscalate, AlertRead
from app.schemas.base import PaginatedResponse


class AlertService:
    def __init__(
        self,
        alert_repo: AlertRepository,
        case_repo: CaseRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self.repo = alert_repo
        self.case_repo = case_repo
        self.audit_repo = audit_repo

    async def get_by_id(self, alert_id: UUID) -> AlertRead:
        alert = await self._get_or_404(alert_id)
        return AlertRead.model_validate(alert)

    async def list_alerts(
        self,
        *,
        severity: str | None = None,
        status: str | None = None,
        alert_type: str | None = None,
        limit: int = 25,
        cursor: str | None = None,
    ) -> PaginatedResponse[AlertRead]:
        parsed_cursor = decode_cursor(cursor) if cursor else None
        rows = await self.repo.search(
            severity=severity,
            status=status,
            alert_type=alert_type,
            limit=limit,
            cursor=parsed_cursor,
        )
        items, next_cursor = paginate(rows, limit)
        return PaginatedResponse(
            items=[AlertRead.model_validate(a) for a in items],
            next_cursor=next_cursor,
            limit=limit,
        )

    async def list_for_customer(
        self, customer_id: UUID, *, cursor: Cursor | None = None, limit: int = 25
    ) -> list[Alert]:
        """Raw rows for a customer's alerts — backs CustomerService's
        /customers/{id}/alerts endpoint so that query lives in one place."""
        return await self.repo.list_by_customer(customer_id, cursor=cursor, limit=limit)

    async def dismiss(self, alert_id: UUID, data: AlertDismiss, actor: User) -> AlertRead:
        alert = await self._get_or_404(alert_id)
        if alert.status in ("dismissed", "escalated"):
            raise ConflictError("Alert already resolved")
        alert.status = "dismissed"
        alert.dismissal_reason = data.reason
        alert.resolved_at = datetime.now(UTC)
        await self.repo.session.flush()
        await self.repo.session.refresh(alert)
        await self.audit_repo.record(
            actor_id=actor.id,
            action="dismiss",
            resource_type="alert",
            resource_id=alert.id,
            metadata={"reason": data.reason},
        )
        return AlertRead.model_validate(alert)

    async def escalate(
        self, alert_id: UUID, data: AlertEscalate, actor: User
    ) -> AlertRead:
        alert = await self._get_or_404(alert_id)
        if alert.status == "dismissed":
            raise ConflictError("Alert is dismissed")

        case_id = data.case_id
        if case_id is None and data.create_case:
            case_number = await self.case_repo.next_case_number()
            case = Case(
                case_number=case_number,
                customer_id=alert.customer_id,
                owner_id=actor.id,
                case_type=data.case_type,
                priority=data.priority,
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

        alert.status = "escalated"
        alert.case_id = case_id
        alert.resolved_at = datetime.now(UTC)
        await self.repo.session.flush()
        await self.repo.session.refresh(alert)
        await self.audit_repo.record(
            actor_id=actor.id,
            action="escalate",
            resource_type="alert",
            resource_id=alert.id,
            metadata={"case_id": str(case_id)},
        )
        return AlertRead.model_validate(alert)

    async def _get_or_404(self, alert_id: UUID) -> Alert:
        alert = await self.repo.get_active_by_id(alert_id)
        if alert is None:
            raise NotFoundError("alert", alert_id)
        return alert
