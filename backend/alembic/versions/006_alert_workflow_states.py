"""Alert workflow states: new, assigned, escalated, resolved

Revision ID: 006_alert_workflow
Revises: 005_customer_indexes
Create Date: 2026-08-31
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006_alert_workflow"
down_revision: str | None = "005_customer_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("alerts", sa.Column("assignee_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_alerts_assignee_id_users",
        "alerts",
        "users",
        ["assignee_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_alerts_assignee_id",
        "alerts",
        ["assignee_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.execute("UPDATE alerts SET status = 'assigned' WHERE status = 'under_review'")
    op.execute("UPDATE alerts SET status = 'resolved' WHERE status = 'dismissed'")

    op.drop_constraint("ck_alert_dismissal_reason", "alerts", type_="check")
    op.create_check_constraint(
        "ck_alert_resolution_reason",
        "alerts",
        "status <> 'resolved' OR dismissal_reason IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_constraint("ck_alert_resolution_reason", "alerts", type_="check")
    op.create_check_constraint(
        "ck_alert_dismissal_reason",
        "alerts",
        "status <> 'dismissed' OR dismissal_reason IS NOT NULL",
    )

    op.execute("UPDATE alerts SET status = 'under_review' WHERE status = 'assigned'")
    op.execute("UPDATE alerts SET status = 'dismissed' WHERE status = 'resolved'")

    op.drop_index("ix_alerts_assignee_id", table_name="alerts")
    op.drop_constraint("fk_alerts_assignee_id_users", "alerts", type_="foreignkey")
    op.drop_column("alerts", "assignee_id")
