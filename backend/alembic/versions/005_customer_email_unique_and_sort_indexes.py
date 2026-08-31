"""Customer email uniqueness and keyset-friendly indexes for search/sort

Revision ID: 005_customer_indexes
Revises: 004_auth_hardening
Create Date: 2026-08-31

customers.email had no unique constraint even though CustomerService.create/
update enforce "one customer per email" — a check-then-write race could
produce duplicates. Also, /customers?sort=... and the new status/kyc_status
filters had no supporting indexes, so every non-risk_tier sort or filter was
a full scan (or, worse for sort, a full sort of the filtered set on every
page). One composite (column, id) index per sortable field replaces the
single-column risk_tier index and adds the five that were missing.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "005_customer_indexes"
down_revision: str | None = "004_auth_hardening"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ux_customers_email_active",
        "customers",
        ["email"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.drop_index("ix_customers_risk_tier", table_name="customers")

    for column in ("created_at", "updated_at", "full_name", "risk_tier", "status", "kyc_status"):
        op.create_index(
            f"ix_customers_{column}_id",
            "customers",
            [column, "id"],
            postgresql_where=sa.text("deleted_at IS NULL"),
        )


def downgrade() -> None:
    for column in ("created_at", "updated_at", "full_name", "risk_tier", "status", "kyc_status"):
        op.drop_index(f"ix_customers_{column}_id", table_name="customers")

    op.create_index(
        "ix_customers_risk_tier",
        "customers",
        ["risk_tier"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.drop_index("ux_customers_email_active", table_name="customers")
