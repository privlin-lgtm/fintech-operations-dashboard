"""Customer records are synced read-only from the core banking/KYC system in v1
(see docs/requirements.md §3 non-goals) — there is deliberately no
CustomerCreate/CustomerUpdate schema here."""

from pydantic import Field, field_validator

from app.schemas.account import AccountRead
from app.schemas.alert import AlertRead
from app.schemas.base import ORMModel, TimestampSchema, UUIDSchema
from app.schemas.case import CaseRead


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

    # Masked by default per SEC-3 (least privilege / data minimization). An
    # explicit, audit-logged "reveal" action is the follow-up, not this endpoint.
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


class CustomerSearchParams(ORMModel):
    q: str | None = Field(default=None, max_length=100)
    limit: int = Field(default=25, ge=1, le=200)
    cursor: str | None = None
