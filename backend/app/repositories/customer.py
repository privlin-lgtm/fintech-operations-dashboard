from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    model = Customer

    def _active(self):
        return select(Customer).where(Customer.deleted_at.is_(None))

    async def get_active_by_id(self, customer_id: UUID) -> Customer | None:
        result = await self.session.execute(
            self._active().where(Customer.id == customer_id)
        )
        return result.scalar_one_or_none()

    async def get_profile(self, customer_id: UUID) -> Customer | None:
        stmt = (
            self._active()
            .options(
                selectinload(Customer.accounts),
                selectinload(Customer.cases),
                selectinload(Customer.alerts),
            )
            .where(Customer.id == customer_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        *,
        query: str | None,
        limit: int,
        offset: int,
    ) -> list[Customer]:
        stmt = self._active().order_by(Customer.created_at.desc())
        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Customer.full_name.ilike(pattern),
                    Customer.email.ilike(pattern),
                    Customer.phone.ilike(pattern),
                    func.cast(Customer.id, type_=Customer.id.type).ilike(pattern),
                )
            )
        result = await self.session.execute(stmt.limit(limit + 1).offset(offset))
        return list(result.scalars().all())
