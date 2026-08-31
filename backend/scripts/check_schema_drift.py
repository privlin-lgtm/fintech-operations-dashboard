"""Fail if db/schema.sql has drifted from what `alembic upgrade head` actually
builds.

db/schema.sql is a hand-maintained, readable reference alongside the real
source of truth (the Alembic migrations) — nothing enforced that the two
stayed in sync, and they didn't (see migrations 008/009, which exist because
this script's manual precursor caught 10 missing indexes, all ten
updated_at triggers, and two missing CHECK constraints that schema.sql had
documented for years but no migration had ever actually created).

Compares two already-built Postgres databases structurally: tables, columns
(type + nullability), indexes (by name + covered columns), and CHECK
constraints (by name + definition). Deliberately ignores things that
legitimately differ between the two files without being real drift — the
`alembic_version` bookkeeping table, and any PRIMARY KEY / UNIQUE / FOREIGN
KEY constraint auto-naming Postgres does differently for an inline `unique`
column vs an explicit `create unique index` (both files use the explicit
form everywhere on purpose, so this shouldn't come up, but the check only
opines on CHECK constraints and indexes, not every constraint type, to avoid
false positives from constraint-naming style rather than actual schema
differences).

Usage:
    python scripts/check_schema_drift.py <schema_sql_database_url> <alembic_database_url>

Both databases must already have the respective DDL applied — this script
only compares, it doesn't build anything. See .github/workflows/backend-ci.yml
for how CI wires this up against two freshly created databases.
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine

_IGNORED_TABLES = {"alembic_version"}


async def _reflect(url: str) -> dict:
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda c: inspect(c).get_table_names())
        tables = [t for t in tables if t not in _IGNORED_TABLES]
        columns = {
            t: {c["name"]: (str(c["type"]), c["nullable"]) for c in await conn.run_sync(lambda c, t=t: inspect(c).get_columns(t))}
            for t in tables
        }
        indexes = {
            t: {ix["name"]: tuple(ix["column_names"]) for ix in await conn.run_sync(lambda c, t=t: inspect(c).get_indexes(t))}
            for t in tables
        }
        check_rows = (
            await conn.execute(
                text(
                    """
                    SELECT conrelid::regclass::text AS table_name, conname,
                           pg_get_constraintdef(oid) AS definition
                    FROM pg_constraint
                    WHERE contype = 'c' AND connamespace = 'public'::regnamespace
                    """
                )
            )
        ).all()
        checks: dict[str, dict[str, str]] = {}
        for row in check_rows:
            checks.setdefault(row.table_name, {})[row.conname] = row.definition
    await engine.dispose()
    return {"tables": set(tables), "columns": columns, "indexes": indexes, "checks": checks}


def _diff(sql_schema: dict, alembic_schema: dict) -> list[str]:
    problems: list[str] = []

    only_sql = sql_schema["tables"] - alembic_schema["tables"]
    only_alembic = alembic_schema["tables"] - sql_schema["tables"]
    if only_sql:
        problems.append(f"Tables only in schema.sql: {sorted(only_sql)}")
    if only_alembic:
        problems.append(f"Tables only in alembic head: {sorted(only_alembic)}")

    for table in sorted(sql_schema["tables"] & alembic_schema["tables"]):
        sql_cols = sql_schema["columns"][table]
        alembic_cols = alembic_schema["columns"][table]
        if missing := set(sql_cols) - set(alembic_cols):
            problems.append(f"{table}: columns only in schema.sql: {sorted(missing)}")
        if extra := set(alembic_cols) - set(sql_cols):
            problems.append(f"{table}: columns only in alembic head: {sorted(extra)}")
        for col in sorted(set(sql_cols) & set(alembic_cols)):
            if sql_cols[col] != alembic_cols[col]:
                problems.append(
                    f"{table}.{col}: schema.sql={sql_cols[col]} alembic={alembic_cols[col]}"
                )

        sql_idx = sql_schema["indexes"][table]
        alembic_idx = alembic_schema["indexes"][table]
        if missing := set(sql_idx) - set(alembic_idx):
            problems.append(f"{table}: indexes only in schema.sql: {sorted(missing)}")
        if extra := set(alembic_idx) - set(sql_idx):
            problems.append(f"{table}: indexes only in alembic head: {sorted(extra)}")

        sql_checks = sql_schema["checks"].get(table, {})
        alembic_checks = alembic_schema["checks"].get(table, {})
        if missing := set(sql_checks) - set(alembic_checks):
            problems.append(f"{table}: CHECK constraints only in schema.sql: {sorted(missing)}")
        if extra := set(alembic_checks) - set(sql_checks):
            problems.append(f"{table}: CHECK constraints only in alembic head: {sorted(extra)}")

    return problems


async def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2

    sql_url, alembic_url = sys.argv[1], sys.argv[2]
    sql_schema, alembic_schema = await asyncio.gather(_reflect(sql_url), _reflect(alembic_url))
    problems = _diff(sql_schema, alembic_schema)

    if problems:
        print("db/schema.sql has drifted from `alembic upgrade head`:\n")
        for problem in problems:
            print(f"  - {problem}")
        print(
            "\nUpdate db/schema.sql to match the migrations (or add a migration if the "
            "schema itself needs to change) — whichever one is wrong, fix it in this PR."
        )
        return 1

    print("db/schema.sql matches `alembic upgrade head` — no drift found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
