import os
from collections.abc import AsyncGenerator

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/fintech_ops_test"
)

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.core.dependencies import get_session
from app.core.security import hash_password
from app.main import create_app
from app.models.customer import Customer
from app.models.role import Role
from app.models.user import User

settings = get_settings()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """One test = one transaction, rolled back at the end. Every write a test
    or the app makes during the request is visible within the test but never
    reaches the database permanently — tests can't leak state into each other.

    The engine is created (and disposed) inside this function-scoped fixture
    rather than at module level: pytest-asyncio gives each test its own event
    loop, and an asyncpg connection pool created under one loop breaks when a
    later test's loop tries to reuse it.
    """
    engine = create_async_engine(str(settings.database_url), pool_pre_ping=True)
    connection = await engine.connect()
    trans = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint")

    yield session

    await session.close()
    await trans.rollback()
    await connection.close()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = _override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def make_role(db_session: AsyncSession):
    from sqlalchemy import select

    async def _make(name: str = "analyst", permissions: dict | None = None) -> Role:
        result = await db_session.execute(
            select(Role).where(Role.name == name, Role.deleted_at.is_(None))
        )
        role = result.scalar_one_or_none()
        if role is not None:
            return role
        role = Role(name=name, permissions=permissions or {})
        db_session.add(role)
        await db_session.flush()
        return role

    return _make


@pytest_asyncio.fixture
async def make_user(db_session: AsyncSession, make_role):
    async def _make(
        *,
        email: str = "analyst@example.com",
        password: str = "correct-horse-battery",
        role_name: str = "analyst",
        mfa_enabled: bool = False,
        mfa_secret: str | None = None,
    ) -> User:
        role = await make_role(role_name)
        user = User(
            role_id=role.id,
            email=email,
            full_name="Test User",
            hashed_password=hash_password(password),
            mfa_enabled=mfa_enabled,
            mfa_secret=mfa_secret,
        )
        db_session.add(user)
        await db_session.flush()
        user.role = role
        return user

    return _make


@pytest_asyncio.fixture
async def make_customer(db_session: AsyncSession):
    async def _make(*, full_name: str = "Jon Smith", **kwargs) -> Customer:
        customer = Customer(full_name=full_name, **kwargs)
        db_session.add(customer)
        await db_session.flush()
        return customer

    return _make


@pytest_asyncio.fixture
async def make_account(db_session: AsyncSession, make_customer):
    from app.models.account import Account

    async def _make(*, customer_id=None, **kwargs) -> Account:
        if customer_id is None:
            customer = await make_customer()
            customer_id = customer.id
        account = Account(customer_id=customer_id, **kwargs)
        if "account_type" not in kwargs:
            account.account_type = "checking"
        if "masked_number" not in kwargs:
            account.masked_number = "**** 4471"
        db_session.add(account)
        await db_session.flush()
        return account

    return _make


@pytest_asyncio.fixture
async def make_transaction(db_session: AsyncSession, make_account):
    from app.models.transaction import Transaction

    async def _make(*, account_id=None, **kwargs) -> Transaction:
        if account_id is None:
            account = await make_account()
            account_id = account.id
        txn = Transaction(account_id=account_id, **kwargs)
        if "amount_cents" not in kwargs:
            txn.amount_cents = 10_000
        if "direction" not in kwargs:
            txn.direction = "debit"
        if "channel" not in kwargs:
            txn.channel = "card"
        db_session.add(txn)
        await db_session.flush()
        return txn

    return _make


@pytest_asyncio.fixture
async def make_case(db_session: AsyncSession, make_customer):
    from datetime import UTC, datetime, timedelta

    from app.models.case import Case
    from app.repositories.case import CaseRepository

    repo = CaseRepository(db_session)

    async def _make(*, customer_id=None, **kwargs) -> Case:
        if customer_id is None:
            customer = await make_customer()
            customer_id = customer.id
        case_number = await repo.next_case_number()
        case = Case(case_number=case_number, customer_id=customer_id, case_type="fraud", **kwargs)
        if "status" not in kwargs:
            case.status = "new"
        if "priority" not in kwargs:
            case.priority = "medium"
        if "sla_due_at" not in kwargs and case.sla_due_at is None:
            case.sla_due_at = datetime.now(UTC) + timedelta(hours=72)
        if case.status.startswith("closed"):
            if case.resolution_code is None:
                case.resolution_code = "fraud_confirmed"
            if case.closing_summary is None:
                case.closing_summary = "Closed in test fixture"
            if case.closed_at is None:
                case.closed_at = datetime.now(UTC)
        db_session.add(case)
        await db_session.flush()
        return case

    return _make


@pytest_asyncio.fixture
async def make_alert(db_session: AsyncSession, make_customer):
    from datetime import UTC, datetime

    from app.models.alert import Alert

    async def _make(*, customer_id=None, **kwargs) -> Alert:
        if customer_id is None:
            customer = await make_customer()
            customer_id = customer.id
        alert = Alert(
            customer_id=customer_id,
            alert_type=kwargs.pop("alert_type", "manual_watchlist"),
            severity=kwargs.pop("severity", "low"),
            triggering_reason=kwargs.pop("triggering_reason", "Test alert"),
            **kwargs,
        )
        if "status" not in kwargs:
            alert.status = "new"
        if alert.status == "resolved":
            if alert.dismissal_reason is None:
                alert.dismissal_reason = "Resolved in test fixture"
            if alert.resolved_at is None:
                alert.resolved_at = datetime.now(UTC)
        db_session.add(alert)
        await db_session.flush()
        return alert

    return _make

