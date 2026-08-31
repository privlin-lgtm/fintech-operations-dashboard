from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.case import Case, CaseNote, CaseTransactionLink
from app.repositories.base import BaseRepository


class CaseRepository(BaseRepository[Case]):
    model = Case

    def _active(self):
        return select(Case).where(Case.deleted_at.is_(None))

    async def get_detail(self, case_id: UUID) -> Case | None:
        stmt = (
            self._active()
            .options(selectinload(Case.notes))
            .where(Case.id == case_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_customer(self, customer_id: UUID) -> list[Case]:
        stmt = (
            self._active()
            .where(Case.customer_id == customer_id)
            .order_by(Case.created_at.desc())
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
        offset: int,
    ) -> list[Case]:
        stmt = self._active().order_by(Case.created_at.desc())
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
        result = await self.session.execute(stmt.limit(limit + 1).offset(offset))
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
