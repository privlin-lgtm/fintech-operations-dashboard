from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.pagination import Cursor
from app.models.alert import Alert
from app.models.case import Case, CaseNote, CaseTransactionLink
from app.repositories.base import BaseRepository


class CaseRepository(BaseRepository[Case]):
    model = Case

    async def get_detail(self, case_id: UUID) -> Case | None:
        stmt = self._base_query().options(selectinload(Case.notes)).where(Case.id == case_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_customer(
        self, customer_id: UUID, *, cursor: Cursor | None = None, limit: int = 25
    ) -> list[Case]:
        stmt = self._base_query().where(Case.customer_id == customer_id)
        stmt = self._keyset_page(stmt, cursor=cursor, limit=limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_recent_by_customer(self, customer_id: UUID, *, limit: int = 5) -> list[Case]:
        stmt = (
            self._base_query()
            .where(Case.customer_id == customer_id)
            .order_by(Case.created_at.desc(), Case.id.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self,
        *,
        status: str | None = None,
        priority: str | None = None,
        assignee: UUID | None = None,
        sla_risk: bool | None = None,
        limit: int,
        cursor: Cursor | None = None,
    ) -> list[Case]:
        stmt = self._base_query()
        if status:
            stmt = stmt.where(Case.status == status)
        if priority:
            stmt = stmt.where(Case.priority == priority)
        if assignee:
            stmt = stmt.where(Case.owner_id == assignee)
        if sla_risk:
            now = datetime.now(UTC)
            stmt = stmt.where(
                Case.sla_due_at.is_not(None),
                Case.sla_due_at <= now,
                Case.status.not_like("closed%"),
            )
        stmt = self._keyset_page(stmt, cursor=cursor, limit=limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def next_case_number(self) -> str:
        year = datetime.now(UTC).year
        prefix = f"CASE-{year}-"
        result = await self.session.execute(
            select(func.count()).select_from(Case).where(Case.case_number.like(f"{prefix}%"))
        )
        count = result.scalar_one()
        return f"{prefix}{count + 1:06d}"

    async def add_note(self, note: CaseNote) -> CaseNote:
        self.session.add(note)
        await self.session.flush()
        await self.session.refresh(note)
        return note

    async def link_transaction(self, link: CaseTransactionLink) -> CaseTransactionLink:
        self.session.add(link)
        await self.session.flush()
        return link

    async def link_alert(self, case_id: UUID, alert_id: UUID) -> Alert | None:
        result = await self.session.execute(
            select(Alert).where(Alert.id == alert_id, Alert.deleted_at.is_(None))
        )
        alert = result.scalar_one_or_none()
        if alert is None:
            return None
        alert.case_id = case_id
        await self.session.flush()
        return alert
