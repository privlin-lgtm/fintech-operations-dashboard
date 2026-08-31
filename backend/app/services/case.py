from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationConflictError
from app.core.pagination import Cursor, decode_cursor, paginate
from app.models.case import Case, CaseNote, CaseTransactionLink
from app.models.user import User
from app.repositories.case import CaseRepository
from app.schemas.base import PaginatedResponse
from app.schemas.case import (
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

SLA_HOURS = {"low": 120, "medium": 72, "high": 24, "critical": 4}


class CaseService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = CaseRepository(session)

    async def create(self, data: CaseCreate, actor: User) -> CaseRead:
        case_number = await self.repo.next_case_number()
        sla_hours = SLA_HOURS.get(data.priority, 72)
        case = Case(
            case_number=case_number,
            customer_id=data.customer_id,
            owner_id=data.owner_id or actor.id,
            case_type=data.case_type,
            priority=data.priority,
            sla_due_at=datetime.now(UTC) + timedelta(hours=sla_hours),
        )
        created = await self.repo.add(case)
        await self.repo.add_note(
            CaseNote(
                case_id=created.id,
                author_id=actor.id,
                body=f"Case created by {actor.full_name}",
                is_system=True,
            )
        )
        return CaseRead.model_validate(created)

    async def get_detail(self, case_id: UUID) -> CaseDetail:
        case = await self.repo.get_detail(case_id)
        if case is None:
            raise NotFoundError("case", case_id)
        return CaseDetail.model_validate(case)

    async def list_cases(
        self,
        *,
        status: str | None = None,
        priority: str | None = None,
        assignee: UUID | None = None,
        sla_risk: bool | None = None,
        limit: int = 25,
        cursor: str | None = None,
    ) -> PaginatedResponse[CaseRead]:
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
        """Raw rows for a customer's cases — the single query CustomerService's
        /customers/{id}/cases endpoint builds its paginated response from."""
        return await self.repo.list_by_customer(customer_id, cursor=cursor, limit=limit)

    async def update(self, case_id: UUID, data: CaseUpdate, actor: User) -> CaseRead:
        case = await self._get_or_404(case_id)
        if data.status and data.status != case.status:
            allowed = VALID_TRANSITIONS.get(case.status, set())
            if data.status not in allowed:
                raise ValidationConflictError(
                    f"Cannot transition from {case.status!r} to {data.status!r}"
                )
            case.status = data.status
            await self.repo.add_note(
                CaseNote(
                    case_id=case.id,
                    author_id=actor.id,
                    body=f"Status changed to {data.status}",
                    is_system=True,
                )
            )
        if data.priority:
            case.priority = data.priority
        if data.owner_id is not None:
            case.owner_id = data.owner_id
        await self.repo.session.flush()
        await self.repo.session.refresh(case)
        return CaseRead.model_validate(case)

    async def add_note(self, case_id: UUID, data: CaseNoteCreate, actor: User) -> CaseDetail:
        case = await self._get_or_404(case_id)
        await self.repo.add_note(
            CaseNote(case_id=case.id, author_id=actor.id, body=data.body)
        )
        return await self.get_detail(case_id)

    async def reassign(self, case_id: UUID, data: CaseReassign, actor: User) -> CaseRead:
        case = await self._get_or_404(case_id)
        case.owner_id = data.owner_id
        await self.repo.add_note(
            CaseNote(
                case_id=case.id,
                author_id=actor.id,
                body=f"Reassigned: {data.reason}",
                is_system=True,
            )
        )
        await self.repo.session.flush()
        await self.repo.session.refresh(case)
        return CaseRead.model_validate(case)

    async def close(self, case_id: UUID, data: CaseClose, actor: User) -> CaseRead:
        case = await self._get_or_404(case_id)
        if case.status.startswith("closed"):
            raise ConflictError("Case already closed")
        case.status = data.status
        case.resolution_code = data.resolution_code
        case.closing_summary = data.closing_summary
        case.closed_at = datetime.now(UTC)
        await self.repo.add_note(
            CaseNote(
                case_id=case.id,
                author_id=actor.id,
                body=f"Case closed: {data.resolution_code}",
                is_system=True,
            )
        )
        await self.repo.session.flush()
        await self.repo.session.refresh(case)
        return CaseRead.model_validate(case)

    async def link(self, case_id: UUID, data: CaseLinkCreate, actor: User) -> CaseDetail:
        case = await self._get_or_404(case_id)
        if data.transaction_id:
            await self.repo.link_transaction(
                CaseTransactionLink(
                    case_id=case.id,
                    transaction_id=data.transaction_id,
                    linked_by=actor.id,
                )
            )
        return await self.get_detail(case_id)

    async def _get_or_404(self, case_id: UUID) -> Case:
        case = await self.repo.get_detail(case_id)
        if case is None:
            raise NotFoundError("case", case_id)
        return case
