"""Refresh tokens, MFA secret/token versioning, and the case/alert check
constraints that db/schema.sql documented but 002 never actually created.

Revision ID: 004_auth_hardening
Revises: 003_audit_log
Create Date: 2026-08-31

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004_auth_hardening"
down_revision: str | None = "003_audit_log"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("mfa_secret", sa.Text(), nullable=True))
    op.add_column(
        "users",
        sa.Column("token_version", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("device_info", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="ux_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # These three were documented in db/schema.sql from the start but never
    # made it into 002_domain_tables — the application layer enforced them,
    # the database didn't. Adding them now as a defense-in-depth backstop.
    op.create_check_constraint(
        "ck_case_closed_requires_resolution",
        "cases",
        "status NOT IN ('closed_resolved', 'closed_no_action') "
        "OR (resolution_code IS NOT NULL AND closing_summary IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_alert_dismissal_reason",
        "alerts",
        "status <> 'dismissed' OR dismissal_reason IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_alert_escalation_has_case",
        "alerts",
        "status <> 'escalated' OR case_id IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_constraint("ck_alert_escalation_has_case", "alerts", type_="check")
    op.drop_constraint("ck_alert_dismissal_reason", "alerts", type_="check")
    op.drop_constraint("ck_case_closed_requires_resolution", "cases", type_="check")

    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_column("users", "token_version")
    op.drop_column("users", "mfa_secret")
