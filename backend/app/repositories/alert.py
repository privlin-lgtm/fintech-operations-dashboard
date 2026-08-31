from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select

from app.models.alert import Alert
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    model = Alert

    def _active(self):
        return select(Alert).where(Alert.deleted_at.is_(None))

    async def get_active_by_id(self, alert_id: UUID) -> Alert | None:
        result = await self.session.execute(
            self._active().where(Alert.id == alert_id)
        )
        return result.scalar_one_or_none()

    async def list_by_customer(self, customer_id: UUID) -> list[Alert]:
        stmt = (
            self._active()
            .where(Alert.customer_id == customer_id)
            .order_by(Alert.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search(
        self,
        *,
        severity: str | None = None,
        status: str | None = None,
        alert_type: str | None = None,
        limit: int,
        offset: int,
    ) -> list[Alert]:
        stmt = self._active().order_by(Alert.created_at.desc())
        if severity:
            stmt = stmt.where(Alert.severity == severity)
        if status:
            stmt = stmt.where(Alert.status == status)
        if alert_type:
            stmt = stmt.where(Alert.alert_type == alert_type)
        result = await self.session.execute(stmt.limit(limit + 1).offset(offset))
        return list(result.scalars().all())

    async def count_by_status(self, status: str) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Alert).where(
                Alert.deleted_at.is_(None), Alert.status == status
            )
        )
        return result.scalar_one()
