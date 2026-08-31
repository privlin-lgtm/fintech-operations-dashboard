"""Add enum-value CHECK constraints db/schema.sql documented but no earlier
migration actually created: alerts.type, alerts.status, reports.report_type,
reports.cadence, and cases.status.

Every other enum-like text column across the domain tables got its CHECK
constraint back in 002/004 — these five didn't, so the database has been
silently accepting any string in them. Found via the same schema-drift
comparison that produced 008.

Revision ID: 009_missing_enum_checks
Revises: 008_missing_triggers_and_indexes
Create Date: 2026-08-31
"""
from collections.abc import Sequence

from alembic import op

revision: str = "009_missing_enum_checks"
down_revision: str | None = "008_missing_triggers_and_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ALERT_TYPE_VALUES = (
    "high_risk_txn",
    "velocity",
    "sanctions_match",
    "login_anomaly",
    "manual_watchlist",
)
_ALERT_STATUS_VALUES = ("new", "assigned", "escalated", "resolved")
_REPORT_TYPE_VALUES = (
    "case_volume",
    "sla_compliance",
    "alert_disposition",
    "analyst_productivity",
    "audit_trail",
)
_REPORT_CADENCE_VALUES = ("once", "daily", "weekly", "monthly")
_CASE_STATUS_VALUES = (
    "new",
    "in_progress",
    "pending_external",
    "escalated",
    "closed_resolved",
    "closed_no_action",
)


def _in_list(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{v}'" for v in values)


def upgrade() -> None:
    op.create_check_constraint(
        "ck_alerts_type", "alerts", f"type IN ({_in_list(_ALERT_TYPE_VALUES)})"
    )
    op.create_check_constraint(
        "ck_alerts_status", "alerts", f"status IN ({_in_list(_ALERT_STATUS_VALUES)})"
    )
    op.create_check_constraint(
        "ck_reports_type", "reports", f"report_type IN ({_in_list(_REPORT_TYPE_VALUES)})"
    )
    # cadence is nullable ("once" reports don't recur); IN() already evaluates
    # to NULL (not FALSE) for a NULL cadence, so the constraint passes as-is.
    op.create_check_constraint(
        "ck_reports_cadence", "reports", f"cadence IN ({_in_list(_REPORT_CADENCE_VALUES)})"
    )
    op.create_check_constraint(
        "ck_cases_status", "cases", f"status IN ({_in_list(_CASE_STATUS_VALUES)})"
    )


def downgrade() -> None:
    op.drop_constraint("ck_cases_status", "cases", type_="check")
    op.drop_constraint("ck_reports_cadence", "reports", type_="check")
    op.drop_constraint("ck_reports_type", "reports", type_="check")
    op.drop_constraint("ck_alerts_status", "alerts", type_="check")
    op.drop_constraint("ck_alerts_type", "alerts", type_="check")
