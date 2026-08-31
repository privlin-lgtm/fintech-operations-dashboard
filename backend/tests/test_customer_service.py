"""Unit tests for Customer Management — service, sorting, schemas.

Service tests use AsyncMock repositories so they don't need Postgres.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import (
    ConflictError,
    InvalidCursorError,
    NotFoundError,
    ValidationConflictError,
)
from app.core.sorting import (
    SortCursor,
    decode_sort_cursor,
    encode_sort_cursor,
    paginate_sorted,
    parse_sort,
)
from app.models.customer import Customer
from app.models.enums import CustomerStatus, KycStatus, RiskTier
from app.models.role import Role
from app.models.user import User
from app.repositories.customer import _escape_like, parse_customer_sort
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.services.customer import CustomerService


def _now() -> datetime:
    return datetime.now(UTC)


def _customer(**overrides) -> Customer:
    c = Customer(
        full_name=overrides.pop("full_name", "Jon Smith"),
        email=overrides.pop("email", "jon@example.com"),
        phone=overrides.pop("phone", "555-123-4567"),
        kyc_status=overrides.pop("kyc_status", "verified"),
        risk_tier=overrides.pop("risk_tier", "low"),
        status=overrides.pop("status", "active"),
    )
    c.id = overrides.pop("id", uuid4())
    c.created_at = overrides.pop("created_at", _now())
    c.updated_at = overrides.pop("updated_at", c.created_at)
    c.deleted_at = overrides.pop("deleted_at", None)
    for k, v in overrides.items():
        setattr(c, k, v)
    return c


def _actor(*, role_name: str = "admin") -> User:
    role = Role(name=role_name, permissions={})
    role.id = uuid4()
    user = User(
        role_id=role.id,
        email="admin@example.com",
        full_name="Admin User",
        hashed_password="x",
    )
    user.id = uuid4()
    user.role = role
    return user


def _service(
    *,
    customer_repo: AsyncMock | None = None,
    audit_repo: AsyncMock | None = None,
) -> tuple[CustomerService, AsyncMock, AsyncMock]:
    customer_repo = customer_repo or AsyncMock()
    customer_repo.session = AsyncMock()
    account_repo = AsyncMock()
    case_repo = AsyncMock()
    case_repo.count.return_value = 0  # "no open cases" by default; override per test
    alert_repo = AsyncMock()
    audit_repo = audit_repo or AsyncMock()
    case_service = AsyncMock()
    alert_service = AsyncMock()
    svc = CustomerService(
        customer_repo=customer_repo,
        account_repo=account_repo,
        case_repo=case_repo,
        alert_repo=alert_repo,
        audit_repo=audit_repo,
        case_service=case_service,
        alert_service=alert_service,
    )
    return svc, customer_repo, audit_repo


# ---------------------------------------------------------------------------
# Sorting helpers
# ---------------------------------------------------------------------------


def test_parse_sort_descending():
    spec = parse_sort("-full_name", allowed={"full_name", "created_at"})
    assert spec.field == "full_name"
    assert spec.descending is True
    assert spec.raw == "-full_name"


def test_parse_sort_rejects_unknown_field():
    with pytest.raises(ValidationConflictError):
        parse_sort("email", allowed={"full_name"})


def test_parse_customer_sort_allows_risk_tier():
    spec = parse_customer_sort("risk_tier")
    assert spec.field == "risk_tier"
    assert spec.descending is False


def test_sort_cursor_roundtrip():
    cid = uuid4()
    encoded = encode_sort_cursor(SortCursor(sort="-full_name", sort_value="Smith", id=cid))
    decoded = decode_sort_cursor(encoded, expected_sort="-full_name")
    assert decoded.id == cid
    assert decoded.sort_value == "Smith"


def test_sort_cursor_rejects_sort_mismatch():
    encoded = encode_sort_cursor(
        SortCursor(sort="-full_name", sort_value="A", id=uuid4())
    )
    with pytest.raises(InvalidCursorError):
        decode_sort_cursor(encoded, expected_sort="full_name")


def test_paginate_sorted_emits_cursor_when_more_pages():
    rows = [_customer(full_name=f"Name {i}") for i in range(6)]
    items, cursor = paginate_sorted(
        rows, 5, sort="full_name", get_sort_value=lambda r: r.full_name
    )
    assert len(items) == 5
    assert cursor is not None
    decoded = decode_sort_cursor(cursor, expected_sort="full_name")
    assert decoded.sort_value == items[-1].full_name
    assert decoded.id == items[-1].id


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


def test_customer_create_defaults():
    data = CustomerCreate(full_name="Ada Lovelace")
    assert data.kyc_status == KycStatus.UNVERIFIED
    assert data.risk_tier == RiskTier.LOW
    assert data.status == CustomerStatus.ACTIVE


def test_customer_update_partial():
    data = CustomerUpdate(risk_tier=RiskTier.HIGH)
    dumped = data.model_dump(exclude_unset=True)
    assert dumped == {"risk_tier": RiskTier.HIGH}


def test_customer_read_masks_pii():
    customer = CustomerRead(
        id=uuid4(),
        created_at=_now(),
        updated_at=_now(),
        full_name="Jon Smith",
        email="jon.smith@example.com",
        phone="555-123-4567",
        kyc_status="verified",
        risk_tier="low",
        status="active",
    )
    assert customer.email == "j********@example.com"
    assert customer.phone == "******4567"


def test_like_escape_neutralizes_wildcards():
    assert _escape_like("50% off_deal") == "50\\% off\\_deal"


# ---------------------------------------------------------------------------
# Service — CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_customer_persists_and_audits():
    svc, repo, audit = _service()
    created = _customer(full_name="Ada Lovelace", email="ada@example.com")
    repo.get_by_email.return_value = None
    repo.add.return_value = created
    actor = _actor()

    result = await svc.create(
        CustomerCreate(full_name="Ada Lovelace", email="ada@example.com"),
        actor=actor,
    )

    repo.add.assert_awaited_once()
    audit.record.assert_awaited_once()
    assert audit.record.await_args.kwargs["action"] == "create"
    assert result.full_name == "Ada Lovelace"
    assert result.email == "a**@example.com"  # masked on read


@pytest.mark.asyncio
async def test_create_customer_rejects_duplicate_email():
    svc, repo, _audit = _service()
    repo.get_by_email.return_value = _customer(email="ada@example.com")

    with pytest.raises(ConflictError):
        await svc.create(
            CustomerCreate(full_name="Ada", email="ada@example.com"),
            actor=_actor(),
        )
    repo.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_customer_applies_fields_and_audits():
    svc, repo, audit = _service()
    existing = _customer(risk_tier="low")
    repo.get_active_by_id.return_value = existing
    actor = _actor()

    result = await svc.update(
        existing.id,
        CustomerUpdate(risk_tier=RiskTier.HIGH, status=CustomerStatus.SUSPENDED),
        actor=actor,
    )

    assert existing.risk_tier == "high"
    assert existing.status == "suspended"
    repo.session.flush.assert_awaited()
    audit.record.assert_awaited_once()
    assert audit.record.await_args.kwargs["action"] == "update"
    assert result.risk_tier == "high"


@pytest.mark.asyncio
async def test_update_customer_not_found():
    svc, repo, _audit = _service()
    missing = uuid4()
    repo.get_active_by_id.return_value = None

    with pytest.raises(NotFoundError):
        await svc.update(missing, CustomerUpdate(full_name="X"), actor=_actor())


@pytest.mark.asyncio
async def test_delete_customer_soft_deletes_and_audits():
    svc, repo, audit = _service()
    existing = _customer()
    repo.get_active_by_id.return_value = existing
    repo.soft_delete.return_value = existing

    await svc.delete(existing.id, actor=_actor())

    repo.soft_delete.assert_awaited_once_with(existing)
    assert audit.record.await_args.kwargs["action"] == "delete"


@pytest.mark.asyncio
async def test_delete_customer_blocked_by_open_cases():
    svc, repo, audit = _service()
    existing = _customer()
    repo.get_active_by_id.return_value = existing
    svc.case_repo.count.return_value = 2

    with pytest.raises(ConflictError):
        await svc.delete(existing.id, actor=_actor())

    repo.soft_delete.assert_not_awaited()
    audit.record.assert_not_awaited()


@pytest.mark.asyncio
async def test_search_applies_filters_and_sort():
    svc, repo, _audit = _service()
    rows = [_customer(full_name="A"), _customer(full_name="B")]
    repo.search.return_value = rows

    result = await svc.search(
        query="smith",
        status="active",
        risk_tier="high",
        kyc_status="verified",
        sort="-full_name",
        limit=25,
    )

    kwargs = repo.search.await_args.kwargs
    assert kwargs["query"] == "smith"
    assert kwargs["status"] == "active"
    assert kwargs["risk_tier"] == "high"
    assert kwargs["kyc_status"] == "verified"
    assert kwargs["sort"].field == "full_name"
    assert kwargs["sort"].descending is True
    assert len(result.items) == 2
    assert result.next_cursor is None


@pytest.mark.asyncio
async def test_get_profile_not_found():
    svc, repo, _audit = _service()
    repo.get_active_by_id.return_value = None

    with pytest.raises(NotFoundError):
        await svc.get_profile(uuid4(), viewer=_actor())
