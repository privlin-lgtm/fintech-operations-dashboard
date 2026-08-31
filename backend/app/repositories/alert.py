from uuid import UUID

from app.core.pagination import Cursor
from app.models.alert import Alert
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    model = Alert

    async def get_active_by_id(self, alert_id: UUID) -> Alert | None:
        result = await self.session.execute(self._base_query().where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def list_by_customer(
        self, customer_id: UUID, *, cursor: Cursor | None = None, limit: int = 25
    ) -> list[Alert]:
        stmt = self._base_query().where(Alert.customer_id == customer_id)
        stmt = self._keyset_page(stmt, cursor=cursor, limit=limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_recent_by_customer(self, customer_id: UUID, *, limit: int = 5) -> list[Alert]:
        stmt = (
            self._base_query()
            .where(Alert.customer_id == customer_id)
            .order_by(Alert.created_at.desc(), Alert.id.desc())
            .limit(limit)
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
        cursor: Cursor | None = None,
    ) -> list[Alert]:
        stmt = self._base_query()
        if severity:
            stmt = stmt.where(Alert.severity == severity)
        if status:
            stmt = stmt.where(Alert.status == status)
        if alert_type:
            stmt = stmt.where(Alert.alert_type == alert_type)
        stmt = self._keyset_page(stmt, cursor=cursor, limit=limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_status(self, status: str) -> int:
        return await self.count(Alert.status == status)
