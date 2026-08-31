from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import decode_cursor, encode_cursor
from app.models.alert import Alert
from app.models.case import Case, CaseNote
from app.models.user import User
from app.repositories.alert import AlertRepository
from app.repositories.case import CaseRepository
from app.schemas.alert import AlertDismiss, AlertEscalate, AlertRead
from app.schemas.base import PaginatedResponse


class AlertService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = AlertRepository(session)
        self.case_repo = CaseRepository(session)

    async def get_by_id(self, alert_id: UUID) -> AlertRead:
        alert = await self.repo.get_active_by_id(alert_id)
        if alert is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
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
        offset = decode_cursor(cursor) if cursor else 0
        rows = await self.repo.search(
            severity=severity,
            status=status,
            alert_type=alert_type,
            limit=limit,
            offset=offset,
        )
        has_more = len(rows) > limit
        items = rows[:limit]
        return PaginatedResponse(
            items=[AlertRead.model_validate(a) for a in items],
            next_cursor=encode_cursor(offset + limit) if has_more else None,
            limit=limit,
        )

    async def dismiss(self, alert_id: UUID, data: AlertDismiss, actor: User) -> AlertRead:
        alert = await self._get_or_404(alert_id)
        if alert.status in ("dismissed", "escalated"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alert already resolved")
        alert.status = "dismissed"
        alert.dismissal_reason = data.reason
        alert.resolved_at = datetime.now(UTC)
        await self.repo.session.flush()
        await self.repo.session.refresh(alert)
        return AlertRead.model_validate(alert)

    async def escalate(
        self, alert_id: UUID, data: AlertEscalate, actor: User
    ) -> AlertRead:
        alert = await self._get_or_404(alert_id)
        if alert.status == "dismissed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alert is dismissed")

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
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Provide case_id or set create_case=true",
            )

        alert.status = "escalated"
        alert.case_id = case_id
        alert.resolved_at = datetime.now(UTC)
        await self.repo.session.flush()
        await self.repo.session.refresh(alert)
        return AlertRead.model_validate(alert)

    async def _get_or_404(self, alert_id: UUID) -> Alert:
        alert = await self.repo.get_active_by_id(alert_id)
        if alert is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
        return alert
