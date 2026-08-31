"""Login lockout: track failed attempts and temporary lockout on users

Revision ID: 007_login_lockout
Revises: 006_alert_workflow
Create Date: 2026-08-31
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "007_login_lockout"
down_revision: str | None = "006_alert_workflow"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "failed_login_attempts",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "users",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
