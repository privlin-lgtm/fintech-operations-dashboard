from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.case_permissions import (
    CLOSED_STATUSES,
    enforce_assign,
    enforce_close,
    enforce_create_owner,
    enforce_modify,
    enforce_note,
    enforce_reassign,
    enforce_view,
    is_closed,
)
from app.core.exceptions import ConflictError, NotFoundError, ValidationConflictError
from app.core.pagination import Cursor, decode_cursor, paginate
from app.core.sla import SLA_HOURS
from app.models.case import Case, CaseNote, CaseTransactionLink
from app.models.user import User
from app.repositories.audit_log import AuditLogRepository
from app.repositories.case import CaseRepository
from app.repositories.customer import CustomerRepository
from app.repositories.user import UserRepository
from app.schemas.base import PaginatedResponse
from app.schemas.case import (
    CaseAssign,
    CaseClose,
    CaseCreate,
    CaseDetail,
    CaseLinkCreate,
    CaseNoteCreate,
    CaseRead,
    CaseReassign,
    CaseUpdate,
)

VALID_TRANSITIONS: dict[str, set[str]] = {
    "new": {"in_progress", "escalated", "closed_no_action"},
    "in_progress": {"pending_external", "escalated", "closed_resolved", "closed_no_action"},
    "pending_external": {"in_progress", "closed_resolved", "closed_no_action"},
    "escalated": {"in_progress", "closed_resolved", "closed_no_action"},
}


class CaseService:
    def __init__(
        self,
        case_repo: CaseRepository,
        audit_repo: AuditLogRepository,
        customer_repo: CustomerRepository,
        user_repo: UserRepository,
    ) -> None:
        self.repo = case_repo
        self.audit_repo = audit_repo
        self.customer_repo = customer_repo
        self.user_repo = user_repo

    async def create(self, data: CaseCreate, actor: User) -> CaseRead:
        customer = await self.customer_repo.get_active_by_id(data.customer_id)
        if customer is None:
            raise NotFoundError("customer", data.customer_id)

        enforce_create_owner(actor, data.owner_id)
        owner_id = data.owner_id or actor.id
        if data.owner_id:
            await self._ensure_active_user(data.owner_id)

        case_number = await self.repo.next_case_number()
        sla_hours = SLA_HOURS.get(data.priority.value, 72)
        case = Case(
            case_number=case_number,
            customer_id=data.customer_id,
            owner_id=owner_id,
            case_type=data.case_type.value,
            priority=data.priority.value,
            sla_due_at=datetime.now(UTC) + timedelta(hours=sla_hours),
        )
        created = await self.repo.add(case)
        await self._add_system_note(
            created.id, actor.id, f"Case created by {actor.full_name}"
        )
        await self._audit(actor, "create", created.id)
        return CaseRead.model_validate(created)

    async def get_detail(self, case_id: UUID, *, viewer: User) -> CaseDetail:
        case = await self._get_or_404(case_id)
        enforce_view(viewer, case)
        await self._audit(viewer, "view", case.id)
        detail = CaseDetail.model_validate(case)
        detail.owner_name = await self._user_display_name(case.owner_id)
        return detail

    async def list_cases(
        self,
        *,
        actor: User,
        status: str | None = None,
        priority: str | None = None,
        assignee: UUID | None = None,
        sla_risk: bool | None = None,
        limit: int = 25,
        cursor: str | None = None,
    ) -> PaginatedResponse[CaseRead]:
        if actor.role.name == "analyst":
            assignee = actor.id
        parsed_cursor = decode_cursor(cursor) if cursor else None
        rows = await self.repo.search(
            status=status,
            priority=priority,
            assignee=assignee,
            sla_risk=sla_risk,
            limit=limit,
            cursor=parsed_cursor,
        )
        items, next_cursor = paginate(rows, limit)
        return PaginatedResponse(
            items=[CaseRead.model_validate(c) for c in items],
            next_cursor=next_cursor,
            limit=limit,
        )

    async def list_for_customer(
        self, customer_id: UUID, *, cursor: Cursor | None = None, limit: int = 25
    ) -> list[Case]:
        return await self.repo.list_by_customer(customer_id, cursor=cursor, limit=limit)

    async def update(self, case_id: UUID, data: CaseUpdate, actor: User) -> CaseRead:
        case = await self._get_or_404(case_id)
        enforce_modify(actor, case)

        if data.status and data.status.value != case.status:
            self._validate_transition(case.status, data.status.value)
            case.status = data.status.value
            await self._add_system_note(
                case.id, actor.id, f"Status changed to {data.status.value}"
            )

        if data.priority:
            case.priority = data.priority.value
            sla_hours = SLA_HOURS.get(data.priority.value, 72)
            case.sla_due_at = datetime.now(UTC) + timedelta(hours=sla_hours)

        await self.repo.session.flush()
        await self.repo.session.refresh(case)
        await self._audit(
            actor,
            "update",
            case.id,
            metadata=data.model_dump(exclude_unset=True, mode="json"),
        )
        return CaseRead.model_validate(case)

    async def assign(self, case_id: UUID, data: CaseAssign, actor: User) -> CaseRead:
        case = await self._get_or_404(case_id)
        enforce_assign(actor, case)
        await self._ensure_active_user(data.owner_id)

        case.owner_id = data.owner_id
        await self._add_system_note(
            case.id, actor.id, f"Assigned to user {data.owner_id}"
        )
        await self.repo.session.flush()
        await self.repo.session.refresh(case)
        await self._audit(
            actor,
            "assign",
            case.id,
            metadata={"owner_id": str(data.owner_id)},
        )
        return CaseRead.model_validate(case)

    async def add_note(self, case_id: UUID, data: CaseNoteCreate, actor: User) -> CaseDetail:
        case = await self._get_or_404(case_id)
        enforce_note(actor, case)
        await self.repo.add_note(
            CaseNote(case_id=case.id, author_id=actor.id, body=data.body)
        )
        await self._audit(actor, "add_note", case.id)
        return await self.get_detail(case_id, viewer=actor)

    async def reassign(self, case_id: UUID, data: CaseReassign, actor: User) -> CaseRead:
        case = await self._get_or_404(case_id)
        enforce_reassign(actor)
        if is_closed(case):
            raise ConflictError("Cannot reassign a closed case")
        await self._ensure_active_user(data.owner_id)

        case.owner_id = data.owner_id
        await self._add_system_note(
            case.id, actor.id, f"Reassigned: {data.reason}"
        )
        await self.repo.session.flush()
        await self.repo.session.refresh(case)
        await self._audit(
            actor,
            "reassign",
            case.id,
            metadata={"new_owner_id": str(data.owner_id), "reason": data.reason},
        )
        return CaseRead.model_validate(case)

    async def close(self, case_id: UUID, data: CaseClose, actor: User) -> CaseRead:
        case = await self._get_or_404(case_id)
        if is_closed(case):
            raise ConflictError("Case already closed")
        enforce_close(actor, case)

        self._validate_transition(case.status, data.status.value, allow_close=True)
        case.status = data.status.value
        case.resolution_code = data.resolution_code
        case.closing_summary = data.closing_summary
        case.closed_at = datetime.now(UTC)
        await self._add_system_note(
            case.id, actor.id, f"Case closed: {data.resolution_code}"
        )
        await self.repo.session.flush()
        await self.repo.session.refresh(case)
        await self._audit(
            actor,
            "close",
            case.id,
            metadata={
                "resolution_code": data.resolution_code,
                "status": data.status.value,
            },
        )
        return CaseRead.model_validate(case)

    async def link(self, case_id: UUID, data: CaseLinkCreate, actor: User) -> CaseDetail:
        case = await self._get_or_404(case_id)
        enforce_modify(actor, case)

        if data.transaction_id:
            await self.repo.link_transaction(
                CaseTransactionLink(
                    case_id=case.id,
                    transaction_id=data.transaction_id,
                    linked_by=actor.id,
                )
            )
        if data.alert_id:
            linked = await self.repo.link_alert(case.id, data.alert_id)
            if linked is None:
                raise NotFoundError("alert", data.alert_id)

        await self._audit(
            actor,
            "link",
            case.id,
            metadata={
                "transaction_id": str(data.transaction_id) if data.transaction_id else None,
                "alert_id": str(data.alert_id) if data.alert_id else None,
            },
        )
        return await self.get_detail(case_id, viewer=actor)

    def _validate_transition(
        self, current: str, target: str, *, allow_close: bool = False
    ) -> None:
        allowed = set(VALID_TRANSITIONS.get(current, set()))
        if allow_close:
            allowed |= CLOSED_STATUSES
        if target not in allowed:
            raise ValidationConflictError(
                f"Cannot transition from {current!r} to {target!r}"
            )

    async def _user_display_name(self, user_id: UUID | None) -> str | None:
        if user_id is None:
            return None
        user = await self.user_repo.get_by_id(user_id)
        return user.full_name if user else None

    async def _ensure_active_user(self, user_id: UUID) -> None:
        user = await self.user_repo.get_active_by_id(user_id)
        if user is None:
            raise NotFoundError("user", user_id)

    async def _get_or_404(self, case_id: UUID) -> Case:
        case = await self.repo.get_detail(case_id)
        if case is None:
            raise NotFoundError("case", case_id)
        return case

    async def _add_system_note(self, case_id: UUID, author_id: UUID, body: str) -> None:
        await self.repo.add_note(
            CaseNote(case_id=case_id, author_id=author_id, body=body, is_system=True)
        )

    async def _audit(
        self,
        actor: User,
        action: str,
        case_id: UUID,
        *,
        metadata: dict | None = None,
    ) -> None:
        await self.audit_repo.record(
            actor_id=actor.id,
            action=action,
            resource_type="case",
            resource_id=case_id,
            metadata=metadata or {},
        )
