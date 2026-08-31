"""Domain tables: customers through reports

Revision ID: 002_domain
Revises: 001_initial
Create Date: 2026-08-31

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "002_domain"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=True),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("date_of_birth_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("kyc_status", sa.Text(), server_default=sa.text("'unverified'"), nullable=False),
        sa.Column("risk_tier", sa.Text(), server_default=sa.text("'low'"), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("kyc_status IN ('unverified','pending','verified','rejected')", name="ck_customers_kyc_status"),
        sa.CheckConstraint("risk_tier IN ('low','medium','high')", name="ck_customers_risk_tier"),
        sa.CheckConstraint("status IN ('active','suspended','closed')", name="ck_customers_status"),
    )
    op.create_index("ix_customers_phone", "customers", ["phone"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("ix_customers_risk_tier", "customers", ["risk_tier"], postgresql_where=sa.text("deleted_at IS NULL"))

    op.create_table(
        "accounts",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("account_type", sa.Text(), nullable=False),
        sa.Column("masked_number", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'active'"), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("account_type IN ('checking','savings','card','loan')", name="ck_accounts_type"),
        sa.CheckConstraint("status IN ('active','closed','frozen')", name="ck_accounts_status"),
    )
    op.create_index("ix_accounts_customer_id", "accounts", ["customer_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("ix_accounts_status", "accounts", ["status"], postgresql_where=sa.text("deleted_at IS NULL"))

    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.CHAR(length=3), server_default=sa.text("'USD'"), nullable=False),
        sa.Column("direction", sa.Text(), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'initiated'"), nullable=False),
        sa.Column("counterparty_masked", sa.Text(), nullable=True),
        sa.Column("risk_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("amount_cents > 0", name="ck_transactions_amount"),
        sa.CheckConstraint("direction IN ('debit','credit')", name="ck_transactions_direction"),
        sa.CheckConstraint("channel IN ('ach','card','wire','internal')", name="ck_transactions_channel"),
        sa.CheckConstraint("status IN ('initiated','pending','settled','failed','reversed')", name="ck_transactions_status"),
    )
    op.create_index("ix_transactions_account_created", "transactions", ["account_id", "created_at"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("ix_transactions_status", "transactions", ["status"], postgresql_where=sa.text("deleted_at IS NULL"))

    op.create_table(
        "cases",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("case_number", sa.Text(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'new'"), nullable=False),
        sa.Column("priority", sa.Text(), server_default=sa.text("'medium'"), nullable=False),
        sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_code", sa.Text(), nullable=True),
        sa.Column("closing_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("type IN ('dispute','fraud','aml_review')", name="ck_cases_type"),
        sa.CheckConstraint("priority IN ('low','medium','high','critical')", name="ck_cases_priority"),
    )
    op.create_index("ux_cases_case_number", "cases", ["case_number"], unique=True)
    op.create_index("ix_cases_customer_id", "cases", ["customer_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("ix_cases_owner_id", "cases", ["owner_id"], postgresql_where=sa.text("deleted_at IS NULL"))

    op.create_table(
        "case_transaction_links",
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), nullable=False),
        sa.Column("linked_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["linked_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("case_id", "transaction_id"),
    )

    op.create_table(
        "case_notes",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_system", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_case_notes_case_id", "case_notes", ["case_id", "created_at"], postgresql_where=sa.text("deleted_at IS NULL"))

    op.create_table(
        "alerts",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), nullable=True),
        sa.Column("case_id", sa.Uuid(), nullable=True),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'new'"), nullable=False),
        sa.Column("triggering_reason", sa.Text(), nullable=False),
        sa.Column("dismissal_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("severity IN ('low','medium','high','critical')", name="ck_alerts_severity"),
    )
    op.create_index("ix_alerts_customer_id", "alerts", ["customer_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("ix_alerts_queue", "alerts", ["status", "severity", "created_at"], postgresql_where=sa.text("deleted_at IS NULL"))

    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("report_type", sa.Text(), nullable=False),
        sa.Column("filters", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("cadence", sa.Text(), nullable=True),
        sa.Column("recipients", postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_created_by", "reports", ["created_by"], postgresql_where=sa.text("deleted_at IS NULL"))


def downgrade() -> None:
    op.drop_index("ix_reports_created_by", table_name="reports")
    op.drop_table("reports")
    op.drop_index("ix_alerts_queue", table_name="alerts")
    op.drop_index("ix_alerts_customer_id", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("ix_case_notes_case_id", table_name="case_notes")
    op.drop_table("case_notes")
    op.drop_table("case_transaction_links")
    op.drop_index("ix_cases_owner_id", table_name="cases")
    op.drop_index("ix_cases_customer_id", table_name="cases")
    op.drop_index("ux_cases_case_number", table_name="cases")
    op.drop_table("cases")
    op.drop_index("ix_transactions_status", table_name="transactions")
    op.drop_index("ix_transactions_account_created", table_name="transactions")
    op.drop_table("transactions")
    op.drop_index("ix_accounts_status", table_name="accounts")
    op.drop_index("ix_accounts_customer_id", table_name="accounts")
    op.drop_table("accounts")
    op.drop_index("ix_customers_risk_tier", table_name="customers")
    op.drop_index("ix_customers_phone", table_name="customers")
    op.drop_table("customers")
