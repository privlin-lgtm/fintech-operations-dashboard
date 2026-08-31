"""Unit tests for Transaction lookup — service, sorting, status history."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.models.account import Account
from app.models.role import Role
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.transaction import parse_transaction_sort
from app.services.transaction import TransactionService, build_status_history


def _now() -> datetime:
    return datetime.now(UTC)


def _transaction(**overrides) -> Transaction:
    txn = Transaction(
        account_id=overrides.pop("account_id", uuid4()),
        amount_cents=overrides.pop("amount_cents", 5000),
        direction=overrides.pop("direction", "debit"),
        channel=overrides.pop("channel", "card"),
        status=overrides.pop("status", "settled"),
    )
    txn.id = overrides.pop("id", uuid4())
    txn.created_at = overrides.pop("created_at", _now())
    txn.updated_at = overrides.pop("updated_at", txn.created_at)
    txn.currency = overrides.pop("currency", "USD")
    txn.counterparty_masked = overrides.pop("counterparty_masked", "**** 1234")
    txn.risk_score = overrides.pop("risk_score", Decimal("12.50"))
    txn.settled_at = overrides.pop("settled_at", txn.created_at)
    for k, v in overrides.items():
        setattr(txn, k, v)
    return txn


def _account(**overrides) -> Account:
    acct = Account(
        customer_id=overrides.pop("customer_id", uuid4()),
        account_type=overrides.pop("account_type", "checking"),
        masked_number=overrides.pop("masked_number", "**** 4471"),
    )
    acct.id = overrides.pop("id", uuid4())
    return acct


def _viewer() -> User:
    role = Role(name="analyst", permissions={})
    role.id = uuid4()
    user = User(
        role_id=role.id,
        email="analyst@example.com",
        full_name="Analyst",
        hashed_password="x",
    )
    user.id = uuid4()
    user.role = role
    return user


def _service(repo: AsyncMock | None = None, audit: AsyncMock | None = None):
    repo = repo or AsyncMock()
    audit = audit or AsyncMock()
    return TransactionService(repo, audit), repo, audit


def test_parse_transaction_sort_defaults_desc_created_at():
    spec = parse_transaction_sort("-created_at")
    assert spec.field == "created_at"
    assert spec.descending is True


def test_build_status_history_includes_initiated_and_terminal():
    created = _now()
    settled = created
    txn = _transaction(status="settled", created_at=created, settled_at=settled, updated_at=settled)
    history = build_status_history(txn)
    assert history[0].status == "initiated"
    assert any(event.status == "settled" for event in history)


@pytest.mark.asyncio
async def test_get_detail_not_found():
    svc, repo, _audit = _service()
    missing = uuid4()
    repo.get_detail.return_value = None

    with pytest.raises(NotFoundError):
        await svc.get_detail(missing, viewer=_viewer())


@pytest.mark.asyncio
async def test_get_detail_records_audit_and_flags():
    svc, repo, audit = _service()
    acct = _account()
    txn = _transaction()
    txn.account = acct
    repo.get_detail.return_value = txn
    repo.count_open_alerts.return_value = 1
    repo.count_open_cases.return_value = 0

    detail = await svc.get_detail(txn.id, viewer=_viewer())

    audit.record.assert_awaited_once()
    assert detail.has_open_alert is True
    assert detail.has_open_case is False
    assert detail.account.masked_number == "**** 4471"
    assert detail.status_history


@pytest.mark.asyncio
async def test_search_passes_filters_and_enriches_flags():
    svc, repo, _audit = _service()
    txn = _transaction()
    repo.search.return_value = [txn]
    repo.has_open_alert.return_value = False
    repo.has_open_case.return_value = True

    result = await svc.search(
        query="1234",
        customer_id=uuid4(),
        status="settled",
        channel="card",
        direction="debit",
        min_amount=100,
        max_amount=50_000,
        sort="-amount_cents",
        limit=10,
    )

    kwargs = repo.search.await_args.kwargs
    assert kwargs["query"] == "1234"
    assert kwargs["status"] == "settled"
    assert kwargs["sort"].field == "amount_cents"
    assert len(result.items) == 1
    assert result.items[0].has_open_case is True
