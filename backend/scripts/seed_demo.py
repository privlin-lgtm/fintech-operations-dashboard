"""Seed a realistic demo dataset for portfolio screenshots and the walkthrough.

This is NOT the test fixture. ``seed_e2e.py`` stays the minimal, deterministic
dataset the Playwright regression suite asserts on; this script builds a
separate, populated operations desk in its own database so the screens in
``docs/`` show the product as it would look in use.

What it creates (deterministic: a fixed RNG seed, timestamps relative to now):

* 5 staff users across the analyst / investigator / team lead / compliance roles
* 48 customers (individuals and businesses) with 1-3 accounts each
* ~600 transactions spread over the last 120 days, mostly low risk, with a
  minority of high-risk wires and card bursts
* 22 cases across every status, with investigation notes, linked transactions,
  some past their SLA and three closed earlier today
* 16 alerts across all types, severities and workflow states
* 3 scheduled reports

The script wipes and re-creates every row in the target database, so it
refuses to run unless the database name ends in ``_demo`` (override with
``DEMO_SEED_ALLOW_ANY_DB=1``). It writes ``frontend/e2e/.demo-seed-data.json``
with credentials and the entity IDs the capture spec navigates to.

Usage:
    createdb fintech_ops_demo
    DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fintech_ops_demo \\
        alembic upgrade head
    DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fintech_ops_demo \\
        python scripts/seed_demo.py
"""

from __future__ import annotations

import asyncio
import json
import os
import random
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.labels import resolution_label
from app.core.security import hash_password
from app.models.account import Account
from app.models.alert import Alert
from app.models.case import Case, CaseNote, CaseTransactionLink
from app.models.customer import Customer
from app.models.report import Report
from app.models.role import Role
from app.models.transaction import Transaction
from app.models.user import User

DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "DemoOps!2026")
EMAIL_DOMAIN = "harbourline.example"
RNG_SEED = 20261029
HISTORY_DAYS = 120

ROLE_NAMES = ("admin", "analyst", "investigator", "team_lead", "compliance_auditor")

# key -> (full name, email local part, role)
STAFF = {
    "team_lead": ("Priya Raman", "priya.raman", "team_lead"),
    "investigator": ("Daniel Okafor", "daniel.okafor", "investigator"),
    "investigator_2": ("Sofia Marchetti", "sofia.marchetti", "investigator"),
    "analyst": ("Marcus Lindqvist", "marcus.lindqvist", "analyst"),
    "compliance": ("Hannah Brooks", "hannah.brooks", "compliance_auditor"),
}

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "frontend" / "e2e" / ".demo-seed-data.json"

FIRST_NAMES = (
    "Olivia", "James", "Amelia", "Noah", "Isla", "Ethan", "Grace", "Samuel", "Chloe",
    "Lucas", "Maya", "Henry", "Zara", "Oliver", "Leah", "Mateo", "Aisha", "Thomas",
    "Elena", "Benjamin", "Nadia", "Ryan", "Freya", "Adrian", "Ines", "Kwame", "Yuki",
)
LAST_NAMES = (
    "Hughes", "Patel", "Nguyen", "Carter", "Moreno", "O'Brien", "Schmidt", "Kim",
    "Walsh", "Adeyemi", "Russo", "Bennett", "Haddad", "Novak", "Fraser", "Duarte",
    "Ishikawa", "Mensah", "Sullivan", "Varga", "Coleman", "Lindgren", "Ahmed",
)
BUSINESSES = (
    "Meridian Capital LLC", "Meridian Freight Partners", "Blue Harbor Logistics Inc",
    "Northgate Dental Group", "Copperline Construction LLC", "Saffron & Sage Catering",
    "Kestrel Analytics Ltd", "Atlas Import Export Co", "Riverside Veterinary Clinic",
    "Pinecrest Property Management", "Lumen Solar Installations", "Halcyon Travel Agency",
    "Granite Peak Outfitters", "Orchid Lane Florists", "Vantage Auto Brokers",
)

CARD_MERCHANTS = (
    "AMAZON MKTPLACE", "WHOLEFOODS MKT", "SHELL OIL", "UBER TRIP", "NETFLIX.COM",
    "TARGET STORE", "DELTA AIR", "APPLE.COM/BILL", "COSTCO WHSE", "STARBUCKS",
    "HOME DEPOT", "CVS PHARMACY", "AIRBNB", "SPOTIFY", "BEST BUY",
)
ACH_COUNTERPARTIES = (
    "PAYROLL ADP", "IRS TREAS 310", "CON EDISON", "STATE FARM INS", "VERIZON WIRELESS",
    "CHASE CARD PMT", "GUSTO PAYROLL", "ZELLE TRANSFER", "VENMO", "QUICKBOOKS PMT",
)
WIRE_COUNTERPARTIES = (
    "GLOBAL TRADE FZE", "PACIFIC RIM SUPPLY", "LANDMARK ESCROW", "HELVETIA TREUHAND AG",
    "SUNRISE METALS HK", "OFFSHORE HOLDINGS", "BALTIC SHIPPING OU", "CEDAR TITLE CO",
)


@dataclass
class DemoState:
    users: dict[str, User] = field(default_factory=dict)
    customers: list[Customer] = field(default_factory=list)
    accounts_by_customer: dict = field(default_factory=dict)
    transactions_by_customer: dict = field(default_factory=dict)
    cases: list[Case] = field(default_factory=list)
    alerts: list[Alert] = field(default_factory=list)


def _masked(rng: random.Random) -> str:
    return f"**** {rng.randint(1000, 9999)}"


def _ts(now: datetime, days_ago: float, rng: random.Random | None = None) -> datetime:
    jitter = timedelta(minutes=rng.randint(0, 600)) if rng else timedelta()
    return now - timedelta(days=days_ago) + jitter


async def _reset(session: AsyncSession) -> None:
    await session.execute(
        text(
            "TRUNCATE audit_logs, refresh_tokens, case_transaction_links, case_notes, "
            "alerts, cases, transactions, accounts, customers, reports, users "
            "RESTART IDENTITY CASCADE"
        )
    )


async def _roles(session: AsyncSession) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for name in ROLE_NAMES:
        role = (
            await session.execute(select(Role).where(Role.name == name, Role.deleted_at.is_(None)))
        ).scalar_one_or_none()
        if role is None:
            role = Role(name=name, description=f"{name.replace('_', ' ').title()} role")
            session.add(role)
            await session.flush()
        roles[name] = role
    return roles


async def _users(session: AsyncSession, state: DemoState, now: datetime) -> None:
    roles = await _roles(session)
    hashed = hash_password(DEMO_PASSWORD)
    for key, (full_name, local, role_name) in STAFF.items():
        user = User(
            role_id=roles[role_name].id,
            email=f"{local}@{EMAIL_DOMAIN}",
            full_name=full_name,
            hashed_password=hashed,
            last_login_at=now - timedelta(hours=2),
        )
        session.add(user)
        state.users[key] = user
    await session.flush()


def _customers(session: AsyncSession, state: DemoState, rng: random.Random, now: datetime) -> None:
    names: list[tuple[str, bool]] = [(b, True) for b in BUSINESSES]
    seen = set()
    while len(names) < 48:
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        if name not in seen:
            seen.add(name)
            names.append((name, False))
    rng.shuffle(names)

    for name, is_business in names:
        slug = "".join(ch for ch in name.lower() if ch.isalnum() or ch == " ").split()
        if is_business:
            email = f"finance@{''.join(slug[:2])}.example"
        else:
            email = f"{slug[0]}.{slug[-1]}@mailbox.example"
        risk = rng.choices(("low", "medium", "high"), weights=(60, 28, 12))[0]
        kyc = rng.choices(("verified", "pending", "unverified", "rejected"), weights=(78, 12, 7, 3))[0]
        status = rng.choices(("active", "suspended", "closed"), weights=(90, 6, 4))[0]
        created = _ts(now, rng.randint(HISTORY_DAYS + 30, HISTORY_DAYS + 900), rng)
        customer = Customer(
            id=uuid4(),
            full_name=name,
            email=email,
            phone=f"+1 {rng.randint(201, 989)}-555-{rng.randint(1000, 9999)}",
            risk_tier=risk,
            kyc_status=kyc,
            status=status,
            created_at=created,
            updated_at=created,
        )
        customer._demo_business = is_business  # type: ignore[attr-defined]
        session.add(customer)
        state.customers.append(customer)


def _accounts(session: AsyncSession, state: DemoState, rng: random.Random) -> None:
    for customer in state.customers:
        business = customer._demo_business  # type: ignore[attr-defined]
        types = ["checking"]
        if rng.random() < 0.6:
            types.append("card")
        if rng.random() < (0.5 if business else 0.35):
            types.append("savings")
        if business and rng.random() < 0.3:
            types.append("loan")
        accounts = []
        for account_type in types:
            status = "frozen" if customer.status == "suspended" and account_type == "checking" else (
                "closed" if customer.status == "closed" else "active"
            )
            account = Account(
                id=uuid4(),
                customer_id=customer.id,
                account_type=account_type,
                masked_number=_masked(rng),
                status=status,
                opened_at=customer.created_at,
            )
            session.add(account)
            accounts.append(account)
        state.accounts_by_customer[customer.id] = accounts


def _transaction(
    rng: random.Random,
    now: datetime,
    account: Account,
    business: bool,
    days_ago: float,
    *,
    channel: str | None = None,
    risk: float | None = None,
    amount_cents: int | None = None,
    counterparty: str | None = None,
    direction: str | None = None,
    jitter: bool = True,
) -> Transaction:
    if channel is None:
        if account.account_type == "card":
            channel = "card"
        elif account.account_type == "savings":
            channel = "internal"
        else:
            channel = rng.choices(("ach", "card", "wire", "internal"), weights=(45, 30, 8 if business else 3, 15))[0]

    if amount_cents is None:
        if channel == "card":
            amount_cents = rng.randint(4_00, 450_00)
        elif channel == "ach":
            amount_cents = rng.randint(150_00, (18_000_00 if business else 4_500_00))
        elif channel == "wire":
            amount_cents = rng.randint(4_000_00, (220_000_00 if business else 40_000_00))
        else:
            amount_cents = rng.randint(100_00, 6_000_00)

    if counterparty is None:
        pool = {
            "card": CARD_MERCHANTS,
            "ach": ACH_COUNTERPARTIES,
            "wire": WIRE_COUNTERPARTIES,
            "internal": ("OWN ACCOUNT TRANSFER",),
        }[channel]
        counterparty = f"{rng.choice(pool)} {_masked(rng)}"

    if direction is None:
        direction = "credit" if (channel == "ach" and rng.random() < 0.35) or (
            channel == "internal" and rng.random() < 0.5
        ) else "debit"

    if risk is None:
        risk = round(min(rng.betavariate(1.6, 9) * 100, 64.0), 2)

    created = _ts(now, days_ago, rng if jitter else None)
    if created > now:
        created = now - timedelta(minutes=rng.randint(5, 90))
    age = now - created
    if age < timedelta(hours=6):
        status = rng.choice(("initiated", "pending"))
    elif age < timedelta(days=2):
        status = rng.choices(("pending", "settled"), weights=(40, 60))[0]
    else:
        status = rng.choices(("settled", "failed", "reversed"), weights=(95, 3, 2))[0]
    settled_at = None
    if status == "settled":
        settled_at = min(created + timedelta(hours=rng.randint(1, 30)), now)
    updated = min(settled_at or created + timedelta(minutes=rng.randint(1, 240)), now)

    return Transaction(
        id=uuid4(),
        account_id=account.id,
        amount_cents=amount_cents,
        currency="USD",
        direction=direction,
        channel=channel,
        status=status,
        counterparty_masked=counterparty,
        risk_score=risk,
        settled_at=settled_at,
        created_at=created,
        updated_at=updated,
    )


def _transactions(session: AsyncSession, state: DemoState, rng: random.Random, now: datetime) -> None:
    for customer in state.customers:
        business = customer._demo_business  # type: ignore[attr-defined]
        txns = []
        for account in state.accounts_by_customer[customer.id]:
            if account.account_type == "loan":
                count = rng.randint(2, 4)
            else:
                count = rng.randint(4, 12) if not business else rng.randint(6, 16)
            for _ in range(count):
                txns.append(
                    _transaction(rng, now, account, business, rng.uniform(0, HISTORY_DAYS))
                )
        state.transactions_by_customer[customer.id] = txns
        session.add_all(txns)


def _flagged_activity(
    session: AsyncSession, state: DemoState, rng: random.Random, now: datetime
) -> dict[str, Transaction]:
    """High-risk transactions that alerts and cases point at."""
    flagged: dict[str, Transaction] = {}
    by_name = {c.full_name: c for c in state.customers}

    def checking(customer: Customer) -> Account:
        return next(a for a in state.accounts_by_customer[customer.id] if a.account_type == "checking")

    specs = [
        # key, customer, days ago, channel, amount, risk, counterparty
        ("wire_offshore", "Meridian Capital LLC", 0.4, "wire", 486_250_00, 94.2, "HELVETIA TREUHAND AG **** 3399"),
        ("wire_metals", "Atlas Import Export Co", 1.5, "wire", 212_900_00, 88.6, "SUNRISE METALS HK **** 7710"),
        ("wire_shipping", "Blue Harbor Logistics Inc", 6.0, "wire", 97_400_00, 81.3, "BALTIC SHIPPING OU **** 2208"),
        ("wire_escrow", "Vantage Auto Brokers", 11.0, "wire", 158_000_00, 76.9, "LANDMARK ESCROW **** 5521"),
        ("ach_structuring", "Halcyon Travel Agency", 3.0, "ach", 9_850_00, 79.4, "ZELLE TRANSFER **** 0193"),
        ("wire_trade", "Meridian Freight Partners", 18.0, "wire", 64_300_00, 72.5, "GLOBAL TRADE FZE **** 8842"),
    ]
    for key, name, days, channel, amount, risk, cp in specs:
        customer = by_name[name]
        txn = _transaction(
            rng, now, checking(customer), True, days,
            channel=channel, amount_cents=amount, risk=risk, counterparty=cp,
            direction="credit" if channel == "ach" else "debit", jitter=False,
        )
        session.add(txn)
        state.transactions_by_customer[customer.id].append(txn)
        flagged[key] = txn
        if key == "ach_structuring":
            # The rest of the structuring pattern: more credits just under $10k.
            for n in range(5):
                extra = _transaction(
                    rng, now, checking(customer), True, days - 0.4 * (n + 1),
                    channel="ach", amount_cents=rng.randint(9_400_00, 9_950_00),
                    risk=round(rng.uniform(55, 70), 2), direction="credit", jitter=False,
                    counterparty=f"ZELLE TRANSFER {_masked(rng)}",
                )
                session.add(extra)
                state.transactions_by_customer[customer.id].append(extra)

    # Card-testing bursts on a few individuals: several small card payments in minutes.
    individuals = [c for c in state.customers if not c._demo_business]  # type: ignore[attr-defined]
    for idx, customer in enumerate(individuals[:3]):
        account = state.accounts_by_customer[customer.id][0]
        base_days = 0.2 + idx * 4
        for n in range(5):
            txn = _transaction(
                rng, now, account, False, base_days - n / 1440, jitter=False,
                channel="card", amount_cents=rng.randint(1_00, 9_99),
                risk=round(rng.uniform(70, 90), 2),
                counterparty=f"{rng.choice(('STEAMGAMES', 'GIFTCARDMALL', 'DIGITAL GOODS'))} {_masked(rng)}",
            )
            session.add(txn)
            state.transactions_by_customer[customer.id].append(txn)
            if n == 0:
                flagged[f"card_burst_{idx}"] = txn
    return flagged


CASE_NOTES = {
    "fraud": [
        "Customer called in disputing recent card activity; card blocked pending review.",
        "Pulled 30-day card history. Five sub-$10 authorisations within four minutes, consistent with card testing.",
        "Merchant descriptors match a known card-testing pattern. Requested replacement card.",
        "Customer confirmed none of the flagged payments were theirs. Provisional credit issued.",
    ],
    "aml_review": [
        "Opened from high-risk wire alert. Beneficiary bank is in a higher-risk jurisdiction.",
        "Requested invoices and the underlying trade contract from the customer's finance team.",
        "Documents received. Invoice values do not reconcile with declared shipment weights.",
        "Escalated to compliance for a second review before any SAR decision.",
        "Customer's stated business activity is consistent with the counterparties seen. No adverse media.",
    ],
    "dispute": [
        "Customer disputes an ACH debit they say was cancelled last month.",
        "Requested proof of cancellation from the customer.",
        "Proof received and forwarded to the originating bank. Awaiting their response.",
        "Originating bank accepted the return. Funds credited back to the customer.",
    ],
}

CLOSINGS = {
    "closed_resolved": {
        "fraud": ("fraud_confirmed", "Card-testing confirmed; card reissued and customer refunded in full."),
        "aml_review": ("activity_explained", "Supporting documents reconcile with the wire activity; no SAR required."),
        "dispute": ("refund_issued", "Originating bank accepted the return and the customer was credited."),
    },
    "closed_no_action": {
        "fraud": ("customer_authorised", "Customer confirmed the payments were genuine; no fraud."),
        "aml_review": ("false_positive", "Counterparty is a long-standing supplier; alert was a false positive."),
        "dispute": ("withdrawn", "Customer withdrew the dispute after locating the original authorisation."),
    },
}


def _cases(
    session: AsyncSession,
    state: DemoState,
    rng: random.Random,
    now: datetime,
    flagged: dict[str, Transaction],
) -> dict[str, Case]:
    by_name = {c.full_name: c for c in state.customers}
    owners = [state.users["investigator"], state.users["investigator_2"], state.users["analyst"]]
    lead = state.users["team_lead"]

    # (key, customer, type, status, priority, opened days ago, sla offset hours from now
    #  (negative = breached), closed days ago, flagged txn key)
    specs = [
        ("aml_meridian", "Meridian Capital LLC", "aml_review", "in_progress", "critical", 0.3, 20, None, "wire_offshore"),
        ("aml_atlas", "Atlas Import Export Co", "aml_review", "escalated", "high", 1.3, -6, None, "wire_metals"),
        ("aml_blueharbor", "Blue Harbor Logistics Inc", "aml_review", "pending_external", "high", 5.5, 30, None, "wire_shipping"),
        ("aml_halcyon", "Halcyon Travel Agency", "aml_review", "in_progress", "high", 2.8, -3, None, "ach_structuring"),
        ("aml_vantage", "Vantage Auto Brokers", "aml_review", "escalated", "medium", 10.5, 52, None, "wire_escrow"),
        ("aml_freight", "Meridian Freight Partners", "aml_review", "closed_no_action", "medium", 17.0, None, 0.1, "wire_trade"),
        ("fraud_burst_0", None, "fraud", "in_progress", "high", 0.15, 10, None, "card_burst_0"),
        ("fraud_burst_1", None, "fraud", "closed_resolved", "medium", 4.0, None, 0.2, "card_burst_1"),
        ("fraud_burst_2", None, "fraud", "closed_resolved", "medium", 8.0, None, 5.0, "card_burst_2"),
    ]
    individuals = [c for c in state.customers if not c._demo_business]  # type: ignore[attr-defined]
    burst_customers = {f"fraud_burst_{i}": individuals[i] for i in range(3)}

    # Background cases on other customers, spread over the history window.
    background_pool = [c for c in state.customers if c.full_name not in {s[1] for s in specs}]
    background_pool = [c for c in background_pool if c not in burst_customers.values()]
    background = [
        ("dispute", "new", "low", 0.5, 70, None),
        ("dispute", "new", "medium", 0.9, 46, None),
        ("fraud", "new", "high", 1.1, -2, None),
        ("dispute", "in_progress", "medium", 3.5, 26, None),
        ("fraud", "in_progress", "medium", 6.0, 8, None),
        ("dispute", "pending_external", "low", 12.0, 96, None),
        ("dispute", "closed_resolved", "low", 9.0, None, 0.25),
        ("fraud", "closed_resolved", "high", 21.0, None, 15.0),
        ("dispute", "closed_resolved", "medium", 34.0, None, 27.0),
        ("aml_review", "closed_no_action", "low", 48.0, None, 40.0),
        ("dispute", "closed_no_action", "low", 63.0, None, 59.0),
        ("fraud", "closed_resolved", "critical", 88.0, None, 80.0),
        ("aml_review", "closed_resolved", "medium", 104.0, None, 92.0),
    ]
    picked = rng.sample(background_pool, len(background))
    for i, (row, customer) in enumerate(zip(background, picked, strict=True)):
        specs.append((f"bg_{i}", customer.full_name, *row, None))

    specs.sort(key=lambda s: -s[5])  # oldest first, so case numbers follow open order
    year = now.year
    cases: dict[str, Case] = {}
    for seq, (key, name, ctype, status, priority, opened, sla_h, closed, txn_key) in enumerate(specs, 1):
        customer = burst_customers[key] if name is None else by_name[name]
        created = now - timedelta(days=opened)
        is_closed = status.startswith("closed")
        closed_at = None
        if is_closed and closed < 1:
            # "Closed today" cases: a point between UTC midnight and now (the
            # dashboard tile counts from UTC midnight), so the tile is right
            # whatever time of day the seed runs.
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            closed_at = today_start + (now - today_start) * (1 - closed)
        elif is_closed:
            closed_at = now - timedelta(days=closed)
        if is_closed:
            sla_due = created + timedelta(hours={"critical": 24, "high": 48, "medium": 72, "low": 120}[priority])
        else:
            sla_due = now + timedelta(hours=sla_h)
        owner = None if status == "new" else rng.choice(owners)
        if ctype == "aml_review" and owner is state.users["analyst"]:
            owner = state.users["investigator"]
        if key == "aml_meridian":
            # The walkthrough signs in as this investigator and works this case.
            owner = state.users["investigator"]
        code, summary = CLOSINGS[status][ctype] if is_closed else (None, None)
        case = Case(
            id=uuid4(),
            case_number=f"CASE-{year}-{seq:06d}",
            customer_id=customer.id,
            owner_id=owner.id if owner else None,
            case_type=ctype,
            status=status,
            priority=priority,
            sla_due_at=sla_due,
            resolution_code=code,
            closing_summary=summary,
            closed_at=closed_at,
            created_at=created,
            updated_at=closed_at or created + (now - created) / 2,
        )
        session.add(case)
        case._demo_owner = owner  # type: ignore[attr-defined]
        case._demo_txn_key = txn_key  # type: ignore[attr-defined]
        case._demo_customer = customer  # type: ignore[attr-defined]
        cases[key] = case
        state.cases.append(case)

    # Notes: a short investigation history proportional to how far the case got.
    progress = {"new": 1, "in_progress": 2, "pending_external": 3, "escalated": 4,
                "closed_resolved": 4, "closed_no_action": 3}
    for case in state.cases:
        end = case.closed_at or now
        bodies = CASE_NOTES[case.case_type][: progress[case.status]]
        if case.case_type == "aml_review" and case.status == "closed_no_action":
            notes = CASE_NOTES["aml_review"]
            bodies = [notes[0], notes[1], notes[4]]
        author = case._demo_owner or lead  # type: ignore[attr-defined]
        span = (end - case.created_at) / (len(bodies) + 1)
        for n, body in enumerate(bodies, 1):
            at = case.created_at + span * n
            session.add(CaseNote(case_id=case.id, author_id=author.id, body=body,
                                 created_at=at, updated_at=at))
        if case.status == "escalated":
            at = case.created_at + span * (len(bodies) + 0.5)
            session.add(CaseNote(case_id=case.id, author_id=lead.id, is_system=True,
                                 body="Case escalated to compliance review.",
                                 created_at=at, updated_at=at))
        if case.closed_at is not None:
            session.add(CaseNote(case_id=case.id, author_id=author.id, is_system=True,
                                 body=f"Case closed: {resolution_label(case.resolution_code)}.",
                                 created_at=case.closed_at, updated_at=case.closed_at))

    # Link transactions: the flagged one, plus a couple of others from the same customer.
    for case in state.cases:
        customer = case._demo_customer  # type: ignore[attr-defined]
        txn_key = case._demo_txn_key  # type: ignore[attr-defined]
        linked = []
        if txn_key:
            linked.append(flagged[txn_key])
        others = [t for t in state.transactions_by_customer[customer.id] if t not in linked]
        linked += rng.sample(others, min(len(others), rng.randint(1, 2)))
        for txn in linked:
            session.add(CaseTransactionLink(
                case_id=case.id, transaction_id=txn.id,
                linked_by=(case._demo_owner or lead).id,  # type: ignore[attr-defined]
            ))
    return cases


def _alerts(
    session: AsyncSession,
    state: DemoState,
    rng: random.Random,
    now: datetime,
    flagged: dict[str, Transaction],
    cases: dict[str, Case],
) -> dict[str, Alert]:
    by_id = {c.id: c for c in state.customers}
    inv, inv2, analyst = state.users["investigator"], state.users["investigator_2"], state.users["analyst"]

    def cust(txn: Transaction) -> Customer:
        return next(c for c in state.customers
                    if txn in state.transactions_by_customer[c.id])

    individuals = [c for c in state.customers if not c._demo_business]  # type: ignore[attr-defined]
    quiet = individuals[3:]
    # key, customer, txn, type, severity, status, assignee, case, hours ago, reason, resolution
    specs = [
        ("sanctions_meridian", cust(flagged["wire_offshore"]), flagged["wire_offshore"], "sanctions_match",
         "critical", "assigned", inv, None, 9,
         "Beneficiary name is a 91% fuzzy match to an OFAC SDN list entry", None),
        ("hr_meridian", cust(flagged["wire_offshore"]), flagged["wire_offshore"], "high_risk_txn",
         "high", "escalated", inv, cases["aml_meridian"], 9.5,
         "Outbound wire of $486,250 is far above this customer's usual wire size", None),
        ("hr_atlas", cust(flagged["wire_metals"]), flagged["wire_metals"], "high_risk_txn",
         "critical", "escalated", inv2, cases["aml_atlas"], 34,
         "Wire to a first-time beneficiary in a higher-risk jurisdiction", None),
        ("velocity_halcyon", cust(flagged["ach_structuring"]), flagged["ach_structuring"], "velocity",
         "high", "assigned", inv2, None, 70,
         "Six ACH credits just under $10,000 within 72 hours", None),
        ("card_burst_0", cust(flagged["card_burst_0"]), flagged["card_burst_0"], "velocity",
         "high", "new", None, None, 4,
         "5 card authorisations under $10 within 4 minutes (card-testing pattern)", None),
        ("card_burst_1", cust(flagged["card_burst_1"]), flagged["card_burst_1"], "velocity",
         "medium", "resolved", analyst, None, 100,
         "4 card authorisations under $10 within 3 minutes", "Linked fraud case confirmed and closed"),
        ("hr_blueharbor", cust(flagged["wire_shipping"]), flagged["wire_shipping"], "high_risk_txn",
         "medium", "assigned", inv, None, 140,
         "Wire beneficiary bank changed since the last payment to this counterparty", None),
        ("hr_vantage", cust(flagged["wire_escrow"]), flagged["wire_escrow"], "high_risk_txn",
         "high", "new", None, None, 2,
         "Round-amount wire to an escrow agent with no prior relationship", None),
        ("hr_freight", cust(flagged["wire_trade"]), flagged["wire_trade"], "high_risk_txn",
         "medium", "resolved", inv, None, 430,
         "Wire to a free-zone trading company", "Long-standing supplier; activity consistent with profile"),
        ("login_1", quiet[0], None, "login_anomaly", "medium", "new", None, None, 1.5,
         "Sign-in from a new device in a country the customer has never logged in from", None),
        ("login_2", quiet[1], None, "login_anomaly", "low", "new", None, None, 6,
         "Three failed MFA attempts followed by a successful sign-in", None),
        ("login_3", quiet[2], None, "login_anomaly", "low", "resolved", analyst, None, 52,
         "Sign-in from a new browser on a known device", "Customer confirmed new laptop"),
        ("watch_1", quiet[3], None, "manual_watchlist", "medium", "assigned", analyst, None, 26,
         "Customer added to watchlist after a returned-mail notice", None),
        ("watch_2", by_id[cases["bg_2"].customer_id], None, "manual_watchlist", "high", "new", None, None, 20,
         "Law-enforcement information request received for this customer", None),
        ("sanctions_2", quiet[4], None, "sanctions_match", "low", "new", None, None, 3,
         "Customer name is a 72% fuzzy match to a PEP list entry", None),
        ("velocity_2", quiet[5], None, "velocity", "medium", "assigned", inv2, None, 30,
         "Eight outbound transfers to new payees in 24 hours", None),
    ]
    alerts: dict[str, Alert] = {}
    for key, customer, txn, atype, severity, status, assignee, case, hours, reason, resolution in specs:
        created = now - timedelta(hours=hours)
        alert = Alert(
            id=uuid4(),
            customer_id=customer.id,
            transaction_id=txn.id if txn else None,
            case_id=case.id if case else None,
            assignee_id=assignee.id if assignee else None,
            alert_type=atype,
            severity=severity,
            status=status,
            triggering_reason=reason,
            dismissal_reason=resolution,
            resolved_at=created + timedelta(hours=rng.randint(2, 20)) if status == "resolved" else None,
            created_at=created,
            updated_at=created,
        )
        session.add(alert)
        alerts[key] = alert
        state.alerts.append(alert)
    return alerts


def _reports(session: AsyncSession, state: DemoState, now: datetime) -> None:
    lead, compliance = state.users["team_lead"], state.users["compliance"]
    specs = [
        ("sla_compliance", "weekly", lead, [f"ops-leads@{EMAIL_DOMAIN}"], {"group_by": "priority"}),
        ("alert_disposition", "daily", compliance, [f"compliance@{EMAIL_DOMAIN}"], {"group_by": "severity"}),
        ("case_volume", "monthly", lead, [f"ops-leads@{EMAIL_DOMAIN}", f"cfo@{EMAIL_DOMAIN}"],
         {"group_by": "case_type"}),
    ]
    for report_type, cadence, owner, recipients, filters in specs:
        session.add(Report(
            report_type=report_type, cadence=cadence, recipients=recipients, filters=filters,
            created_by=owner.id, last_run_at=now - timedelta(days=1),
            next_run_at=now + timedelta(days={"daily": 1, "weekly": 7, "monthly": 30}[cadence]),
        ))


async def seed(session: AsyncSession) -> dict:
    rng = random.Random(RNG_SEED)
    now = datetime.now(UTC)
    state = DemoState()

    await _reset(session)
    await _users(session, state, now)
    _customers(session, state, rng, now)
    await session.flush()
    _accounts(session, state, rng)
    await session.flush()
    _transactions(session, state, rng, now)
    flagged = _flagged_activity(session, state, rng, now)
    await session.flush()
    cases = _cases(session, state, rng, now, flagged)
    await session.flush()
    alerts = _alerts(session, state, rng, now, flagged, cases)
    _reports(session, state, now)
    await session.flush()

    showcase_txn = flagged["wire_offshore"]
    showcase_customer = next(c for c in state.customers if c.full_name == "Meridian Capital LLC")
    txn_count = sum(len(v) for v in state.transactions_by_customer.values())
    return {
        "password": DEMO_PASSWORD,
        "users": {
            key: {"id": str(u.id), "email": u.email, "name": u.full_name}
            for key, u in state.users.items()
        },
        "customerSearch": {"query": "Meridian", "name": showcase_customer.full_name,
                           "id": str(showcase_customer.id)},
        "transaction": {"id": str(showcase_txn.id), "counterparty": showcase_txn.counterparty_masked,
                        "amountLabel": f"${showcase_txn.amount_cents / 100:,.2f}"},
        "case": {"id": str(cases["aml_meridian"].id), "caseNumber": cases["aml_meridian"].case_number},
        # A new, not-yet-assigned case for the walkthrough to triage.
        "triageCase": {"id": str(cases["bg_2"].id), "caseNumber": cases["bg_2"].case_number},
        "alert": {"id": str(alerts["sanctions_meridian"].id),
                  "reason": alerts["sanctions_meridian"].triggering_reason},
        "counts": {
            "customers": len(state.customers),
            "accounts": sum(len(v) for v in state.accounts_by_customer.values()),
            "transactions": txn_count,
            "cases": len(state.cases),
            "alerts": len(state.alerts),
        },
    }


def _check_target(database_url: str) -> None:
    name = make_url(database_url).database or ""
    if not name.endswith("_demo") and os.environ.get("DEMO_SEED_ALLOW_ANY_DB") != "1":
        raise SystemExit(
            f"Refusing to seed {name!r}: seed_demo.py truncates every table, so it only runs "
            "against a database whose name ends in '_demo' (set DEMO_SEED_ALLOW_ANY_DB=1 to override)."
        )


async def main() -> None:
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/fintech_ops_demo",
    )
    _check_target(database_url)
    engine = create_async_engine(database_url, pool_pre_ping=True)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        payload = await seed(session)
        await session.commit()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    counts = payload["counts"]
    print(
        "Demo seed written: "
        + ", ".join(f"{v} {k}" for k, v in counts.items())
        + f". Sign in as {payload['users']['team_lead']['email']}."
    )
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
