"""Customer schemas — search/list with filters & sort, plus CRUD for seed/admin ops.

Read responses mask email/phone by default (SEC-3). An explicit reveal action is
out of scope for this module.
"""

from typing import Literal

from pydantic import EmailStr, Field, field_validator

from app.models.customer import CUSTOMER_SORTABLE_FIELDS
from app.models.enums import CustomerStatus, KycStatus, RiskTier
from app.schemas.account import AccountRead
from app.schemas.alert import AlertRead
from app.schemas.base import ORMModel, TimestampSchema, UUIDSchema
from app.schemas.case import CaseRead

# Fields callers may sort by, derived from the same tuple the repository maps
# to real columns (CUSTOMER_SORTABLE_FIELDS) — one list, not two kept in sync
# by hand. Leading "-" means descending (e.g. "-created_at").
_CUSTOMER_SORT_VALUES = tuple(CUSTOMER_SORTABLE_FIELDS) + tuple(
    f"-{field}" for field in CUSTOMER_SORTABLE_FIELDS
)
CustomerSortField = Literal[*_CUSTOMER_SORT_VALUES]


def _mask_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return email
    local, _, domain = email.partition("@")
    return f"{local[:1]}{'*' * max(len(local) - 1, 1)}@{domain}"


def _mask_phone(phone: str | None) -> str | None:
    if not phone:
        return phone
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) < 4:
        return "*" * len(phone)
    return f"{'*' * (len(digits) - 4)}{digits[-4:]}"


class CustomerRead(UUIDSchema, TimestampSchema):
    full_name: str
    email: str | None = None
    phone: str | None = None
    kyc_status: str
    risk_tier: str
    status: str

    @field_validator("email", mode="before")
    @classmethod
    def _redact_email(cls, value: str | None) -> str | None:
        return _mask_email(value)

    @field_validator("phone", mode="before")
    @classmethod
    def _redact_phone(cls, value: str | None) -> str | None:
        return _mask_phone(value)


class CustomerProfile(CustomerRead):
    account_count: int
    open_case_count: int
    total_case_count: int
    open_alert_count: int
    recent_accounts: list[AccountRead] = []
    recent_cases: list[CaseRead] = []
    recent_alerts: list[AlertRead] = []


class CustomerCreate(ORMModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    kyc_status: KycStatus = KycStatus.UNVERIFIED
    risk_tier: RiskTier = RiskTier.LOW
    status: CustomerStatus = CustomerStatus.ACTIVE


class CustomerUpdate(ORMModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    kyc_status: KycStatus | None = None
    risk_tier: RiskTier | None = None
    status: CustomerStatus | None = None


class CustomerSearchParams(ORMModel):
    q: str | None = Field(default=None, max_length=100)
    status: CustomerStatus | None = None
    risk_tier: RiskTier | None = None
    kyc_status: KycStatus | None = None
    sort: CustomerSortField = "-created_at"
    limit: int = Field(default=25, ge=1, le=200)
    cursor: str | None = None