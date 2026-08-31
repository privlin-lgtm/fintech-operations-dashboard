from datetime import datetime
from uuid import UUID

from app.schemas.base import ORMModel, TimestampSchema, UUIDSchema


class AccountRead(UUIDSchema, TimestampSchema):
    customer_id: UUID
    account_type: str
    masked_number: str
    status: str
    opened_at: datetime
    closed_at: datetime | None = None
