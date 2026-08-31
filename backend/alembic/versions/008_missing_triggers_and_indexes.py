"""Add the updated_at triggers and search/query indexes db/schema.sql has
always documented but no earlier migration actually created.

Found while building a schema-drift check (see scripts/check_schema_drift.py):
comparing a database built from db/schema.sql against one built from
`alembic upgrade head` showed the trigger function and 10 indexes below exist
only in the documentation, never in any migration. None of this is a
behavior change for the app itself — updated_at is already maintained at the
ORM level via TimestampMixin's onupdate=func.now() in app/db/mixins.py — but
that only covers writes made through this application; the trigger is the
defense-in-depth layer schema.sql always claimed existed for any other write
path. The indexes are pure lookup/search performance for query patterns the
application already issues (e.g. FR-CS-2's fuzzy customer search, which
migration 003's own comment already assumed these covered).

Revision ID: 008_missing_triggers_and_indexes
Revises: 007_login_lockout
Create Date: 2026-08-31
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "008_missing_triggers_and_indexes"
down_revision: str | None = "007_login_lockout"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TRIGGERED_TABLES = (
    "roles",
    "users",
    "customers",
    "accounts",
    "transactions",
    "cases",
    "case_notes",
    "alerts",
    "reports",
    "refresh_tokens",
)


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS trigger AS $$
        BEGIN
          NEW.updated_at = now();
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    for table in _TRIGGERED_TABLES:
        op.execute(
            f"CREATE TRIGGER trg_{table}_updated_at "
            f"BEFORE UPDATE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION set_updated_at();"
        )

    # Expression/GIN trigram indexes — raw SQL to match schema.sql exactly,
    # since op.create_index's postgresql_ops keying doesn't cleanly express
    # an operator class on a cast expression like (email::text).
    op.execute(
        "CREATE INDEX ix_customers_email_trgm ON customers "
        "USING gin ((email::text) gin_trgm_ops) WHERE deleted_at IS NULL;"
    )
    op.execute(
        "CREATE INDEX ix_customers_name_trgm ON customers "
        "USING gin (full_name gin_trgm_ops) WHERE deleted_at IS NULL;"
    )

    op.create_index(
        "ix_transactions_amount",
        "transactions",
        ["amount_cents"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_transactions_risk_score",
        "transactions",
        ["risk_score"],
        postgresql_where=sa.text("deleted_at IS NULL AND risk_score IS NOT NULL"),
    )
    op.create_index(
        "ix_cases_status_priority",
        "cases",
        ["status", "priority"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_cases_sla_due_at",
        "cases",
        ["sla_due_at"],
        postgresql_where=sa.text("deleted_at IS NULL AND status NOT LIKE 'closed%'"),
    )
    op.create_index("ix_case_notes_author_id", "case_notes", ["author_id"])
    op.create_index(
        "ix_case_txn_links_transaction", "case_transaction_links", ["transaction_id"]
    )
    op.create_index(
        "ix_alerts_transaction_id",
        "alerts",
        ["transaction_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_reports_next_run_at",
        "reports",
        ["next_run_at"],
        postgresql_where=sa.text("deleted_at IS NULL AND cadence <> 'once'"),
    )


def downgrade() -> None:
    op.drop_index("ix_reports_next_run_at", table_name="reports")
    op.drop_index("ix_alerts_transaction_id", table_name="alerts")
    op.drop_index("ix_case_txn_links_transaction", table_name="case_transaction_links")
    op.drop_index("ix_case_notes_author_id", table_name="case_notes")
    op.drop_index("ix_cases_sla_due_at", table_name="cases")
    op.drop_index("ix_cases_status_priority", table_name="cases")
    op.drop_index("ix_transactions_risk_score", table_name="transactions")
    op.drop_index("ix_transactions_amount", table_name="transactions")
    op.execute("DROP INDEX IF EXISTS ix_customers_name_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_customers_email_trgm;")

    for table in reversed(_TRIGGERED_TABLES):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table};")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at();")
