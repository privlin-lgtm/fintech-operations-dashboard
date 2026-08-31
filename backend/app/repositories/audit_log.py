from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog

    def __init__(self, session: AsyncSession, *, ip_address: str | None = None) -> None:
        super().__init__(session)
        # Captured once per request (see core/dependencies.get_audit_log_repository)
        # so every record() call in a request gets it without threading a
        # Request object through every service method.
        self.ip_address = ip_address

    async def record(
        self,
        *,
        actor_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: UUID,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            log_metadata=metadata or {},
            ip_address=ip_address or self.ip_address,
        )
        return await self.add(entry)
