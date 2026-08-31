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
    async def _make(name: str = "analyst", permissions: dict | None = None) -> Role:
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
