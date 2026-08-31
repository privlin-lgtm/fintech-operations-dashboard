# Fintech Operations Dashboard — Backend

FastAPI backend with SQLAlchemy, PostgreSQL, JWT auth, Alembic migrations, and a layered architecture (repository + service pattern).

## Structure

```
backend/
├── alembic/                  # Database migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/    # Route handlers
│   │       └── router.py     # API v1 router aggregation
│   ├── core/
│   │   ├── config.py         # Pydantic settings
│   │   ├── dependencies.py   # FastAPI dependency injection
│   │   └── security.py       # JWT + password hashing
│   ├── db/
│   │   ├── base.py           # SQLAlchemy declarative base
│   │   ├── mixins.py         # UUID, timestamps, soft-delete
│   │   └── session.py        # Async engine + session factory
│   ├── models/               # SQLAlchemy ORM models
│   ├── repositories/         # Data access layer
│   ├── schemas/              # Pydantic request/response models
│   ├── services/             # Business logic layer
│   └── main.py               # Application entry point
├── tests/
├── .env.example
└── pyproject.toml
```

## Quick start

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e ".[dev]"
copy .env.example .env        # edit DATABASE_URL and JWT_SECRET_KEY
alembic upgrade head
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## API modules

| Module | Prefix | Endpoints |
|--------|--------|-----------|
| Auth | `/api/v1/auth` | login, refresh, logout, me |
| Customers | `/api/v1/customers` | search, profile, accounts, cases, alerts |
| Transactions | `/api/v1/transactions` | get, search |
| Cases | `/api/v1/cases` | CRUD, notes, links, reassign, close |
| Alerts | `/api/v1/alerts` | queue, dismiss, escalate |
| Reports | `/api/v1/reports` | dashboard, case volume, schedules |

Run migrations for all tables:

```bash
alembic upgrade head
```

## Testing

Tests run against a real Postgres database (not SQLite — the schema uses
CITEXT, JSONB, and Postgres-only CHECK constraints that a fake DB can't
validate). Create a dedicated test database once:

```bash
psql -h localhost -U postgres -c "CREATE DATABASE fintech_ops_test;"
```

Then, with `DATABASE_URL` pointed at it:

```bash
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/fintech_ops_test
alembic upgrade head   # once, or after adding a migration
pytest -q
```

Each test runs inside its own transaction (rolled back at the end), so tests
never see each other's data and the test database stays empty between runs.
CI (`.github/workflows/backend-ci.yml`) runs this same flow against a
Postgres service container on every push/PR that touches `backend/`.

## Architecture

- **Models** — SQLAlchemy ORM mapped to PostgreSQL tables
- **Repositories** — Encapsulate database queries; no business logic
- **Services** — Business rules, orchestration, validation
- **Schemas** — Pydantic models for API I/O
- **Dependencies** — Wire layers together via FastAPI `Depends()`
