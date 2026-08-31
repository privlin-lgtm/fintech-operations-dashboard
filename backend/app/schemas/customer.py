from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.account import AccountRead
from app.schemas.alert import AlertRead
from app.schemas.base import ORMModel, TimestampSchema, UUIDSchema
from app.schemas.case import CaseRead


class CustomerRead(UUIDSchema, TimestampSchema):
    full_name: str
    email: EmailStr | None = None
    phone: str | None = None
    kyc_status: str
    risk_tier: str
    status: str


class CustomerProfile(CustomerRead):
    accounts: list[AccountRead] = []
    cases: list[CaseRead] = []
    alerts: list[AlertRead] = []


class CustomerSearchParams(ORMModel):
    q: str | None = None
    limit: int = Field(default=25, ge=1, le=200)
    cursor: str | None = None
