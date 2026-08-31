from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Cursor
from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic async repository providing common CRUD operations."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _base_query(self) -> Select[tuple[ModelT]]:
        stmt = select(self.model)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))  # type: ignore[attr-defined]
        return stmt

    def _keyset_page(
        self, stmt: Select[tuple[ModelT]], *, cursor: Cursor | None, limit: int
    ) -> Select[tuple[ModelT]]:
        """Order and window a query by (created_at, id) for stable, index-backed paging."""
        stmt = stmt.order_by(self.model.created_at.desc(), self.model.id.desc())  # type: ignore[attr-defined]
        if cursor is not None:
            stmt = stmt.where(
                or_(
                    self.model.created_at < cursor.created_at,  # type: ignore[attr-defined]
                    and_(
                        self.model.created_at == cursor.created_at,  # type: ignore[attr-defined]
                        self.model.id < cursor.id,  # type: ignore[attr-defined]
                    ),
                )
            )
        return stmt.limit(limit + 1)

    async def get_by_id(self, entity_id: UUID) -> ModelT | None:
        result = await self.session.execute(
            self._base_query().where(self.model.id == entity_id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[ModelT]:
        result = await self.session.execute(self._base_query().limit(limit).offset(offset))
        return list(result.scalars().all())

    async def count(self, *clauses) -> int:
        stmt = select(func.count()).select_from(self.model)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))  # type: ignore[attr-defined]
        if clauses:
            stmt = stmt.where(*clauses)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        await self.session.delete(entity)
        await self.session.flush()
