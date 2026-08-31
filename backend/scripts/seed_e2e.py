"""Seed deterministic data for Playwright end-to-end tests.

Run before E2E suites (see frontend/e2e/global-setup.ts). Writes
frontend/e2e/.seed-data.json with entity IDs and credentials.

Usage:
    DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fintech_ops_e2e \\
        python scripts/seed_e2e.py
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.models.account import Account
from app.models.alert import Alert
from app.models.case import Case
from app.models.customer import Customer
from app.models.role import Role
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.case import CaseRepository

E2E_PASSWORD = os.environ.get("E2E_PASSWORD", "E2eTest!2026")
E2E_EMAIL_DOMAIN = "e2e-ops.example"
MARKER = "E2E"

ROLE_NAMES = ("admin", "analyst", "investigator", "team_lead", "compliance_auditor")

USERS = {
    "investigator": "e2e-investigator",
    "analyst": "e2e-analyst",
    "team_lead": "e2e-teamlead",
}

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "frontend" / "e2e" / ".seed-data.json"


async def get_or_create_role(session: AsyncSession, name: str) -> Role:
    result = await session.execute(
        select(Role).where(Role.name == name, Role.deleted_at.is_(None))
    )
    role = result.scalar_one_or_none()
    if role is not None:
        return role
    role = Role(name=name, description=f"{name} role for E2E")
    session.add(role)
    await session.flush()
    return role


async def upsert_user(session: AsyncSession, *, slug: str, role: Role) -> User:
    email = f"{slug}@{E2E_EMAIL_DOMAIN}"
    result = await session.execute(
        select(User).where(User.email == email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            role_id=role.id,
            email=email,
            full_name=f"{MARKER} {role.name.replace('_', ' ').title()}",
            hashed_password=hash_password(E2E_PASSWORD),
        )
        session.add(user)
    else:
        user.role_id = role.id
        user.hashed_password = hash_password(E2E_PASSWORD)
        user.full_name = f"{MARKER} {role.name.replace('_', ' ').title()}"
    await session.flush()
    user.role = role
    return user


async def clear_e2e_entities(session: AsyncSession) -> None:
    customers = (
        await session.execute(
            select(Customer.id).where(Customer.full_name.like(f"{MARKER}%"))
        )
    ).scalars().all()
    if not customers:
        return

    await session.execute(delete(Alert).where(Alert.customer_id.in_(customers)))
    await session.execute(delete(Case).where(Case.customer_id.in_(customers)))
    accounts = (
        await session.execute(select(Account.id).where(Account.customer_id.in_(customers)))
    ).scalars().all()
    if accounts:
        await session.execute(delete(Transaction).where(Transaction.account_id.in_(accounts)))
        await session.execute(delete(Account).where(Account.id.in_(accounts)))
    await session.execute(delete(Customer).where(Customer.id.in_(customers)))


async def seed(session: AsyncSession) -> dict:
    roles = {name: await get_or_create_role(session, name) for name in ROLE_NAMES}
    users = {
        key: await upsert_user(session, slug=slug, role=roles[key])
        for key, slug in USERS.items()
    }

    await clear_e2e_entities(session)

    search_customer = Customer(
        full_name=f"{MARKER} Meridian Capital LLC",
        email="treasury@meridian-e2e.example",
        phone="555-010-2999",
        risk_tier="high",
        kyc_status="verified",
        status="active",
    )
    case_customer = Customer(
        full_name=f"{MARKER} Open Case Customer",
        email="cases@open-e2e.example",
        risk_tier="medium",
        kyc_status="verified",
        status="active",
    )
    assign_customer = Customer(
        full_name=f"{MARKER} Assign Case Customer",
        email="assign@case-e2e.example",
        risk_tier="medium",
        kyc_status="verified",
        status="active",
    )
    alert_customer = Customer(
        full_name=f"{MARKER} Alert Triage Customer",
        email="alerts@triage-e2e.example",
        risk_tier="high",
        kyc_status="verified",
        status="active",
    )
    session.add_all([search_customer, case_customer, assign_customer, alert_customer])
    await session.flush()

    account = Account(
        customer_id=search_customer.id,
        account_type="checking",
        masked_number="**** 8821",
        status="active",
    )
    session.add(account)
    await session.flush()

    transaction = Transaction(
        account_id=account.id,
        amount_cents=750_000_00,
        currency="USD",
        direction="debit",
        channel="wire",
        status="pending",
        counterparty_masked="OFFSHORE HOLDINGS **** 3399",
        risk_score=92.5,
    )
    session.add(transaction)
    await session.flush()

    case_repo = CaseRepository(session)
    assign_case_number = await case_repo.next_case_number()
    assign_case = Case(
        case_number=assign_case_number,
        customer_id=assign_customer.id,
        owner_id=users["investigator"].id,
        case_type="fraud",
        status="in_progress",
        priority="high",
        sla_due_at=datetime.now(UTC) + timedelta(hours=48),
    )
    session.add(assign_case)

    alert = Alert(
        customer_id=alert_customer.id,
        transaction_id=transaction.id,
        alert_type="sanctions_match",
        severity="critical",
        status="assigned",
        assignee_id=users["investigator"].id,
        triggering_reason=f"{MARKER} potential OFAC match on beneficiary name",
    )
    session.add(alert)
    await session.flush()

    return {
        "password": E2E_PASSWORD,
        "users": {
            key: {"id": str(user.id), "email": user.email, "role": user.role.name}
            for key, user in users.items()
        },
        "customers": {
            "search": {
                "id": str(search_customer.id),
                "name": search_customer.full_name,
            },
            "openCase": {
                "id": str(case_customer.id),
                "name": case_customer.full_name,
            },
            "assignCase": {
                "id": str(assign_customer.id),
                "name": assign_customer.full_name,
            },
            "alert": {
                "id": str(alert_customer.id),
                "name": alert_customer.full_name,
            },
        },
        "transaction": {
            "id": str(transaction.id),
            "counterparty": transaction.counterparty_masked,
            "amountLabel": "$750,000.00",
        },
        "caseForAssign": {
            "id": str(assign_case.id),
            "caseNumber": assign_case.case_number,
        },
        "alert": {
            "id": str(alert.id),
            "reason": alert.triggering_reason,
        },
    }


async def main() -> None:
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/fintech_ops_e2e",
    )
    engine = create_async_engine(database_url, pool_pre_ping=True)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        payload = await seed(session)
        await session.commit()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("E2E seed data written successfully.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
