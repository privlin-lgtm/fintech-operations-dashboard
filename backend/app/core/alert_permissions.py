"""Alert Management RBAC helpers (SEC-2).

Workflow states: new → assigned → escalated → resolved
- analyst: view assigned alerts + new queue items
- investigator: triage, assign, escalate, resolve
- team_lead / admin: full alert operations
- compliance_auditor: read-only
"""

from app.core.exceptions import AuthorizationError
from app.models.alert import Alert
from app.models.enums import AlertStatus
from app.models.user import User

ALERT_READ_ROLES = ("analyst", "investigator", "team_lead", "compliance_auditor", "admin")
ALERT_CREATE_ROLES = ("investigator", "team_lead", "admin")
ALERT_UPDATE_ROLES = ("investigator", "team_lead", "admin")
ALERT_ASSIGN_ROLES = ("investigator", "team_lead", "admin")
ALERT_ESCALATE_ROLES = ("investigator", "team_lead", "admin")
ALERT_RESOLVE_ROLES = ("investigator", "team_lead", "admin")
ALERT_DELETE_ROLES = ("team_lead", "admin")

OPEN_ALERT_STATUSES = frozenset({
    AlertStatus.NEW.value,
    AlertStatus.ASSIGNED.value,
    AlertStatus.ESCALATED.value,
})

TERMINAL_ALERT_STATUSES = frozenset({AlertStatus.RESOLVED.value})

VALID_TRANSITIONS: dict[str, set[str]] = {
    AlertStatus.NEW.value: {
        AlertStatus.ASSIGNED.value,
        AlertStatus.ESCALATED.value,
        AlertStatus.RESOLVED.value,
    },
    AlertStatus.ASSIGNED.value: {
        AlertStatus.ESCALATED.value,
        AlertStatus.RESOLVED.value,
    },
    AlertStatus.ESCALATED.value: {AlertStatus.RESOLVED.value},
}


def is_terminal(alert: Alert) -> bool:
    return alert.status in TERMINAL_ALERT_STATUSES


def can_view_alert(user: User, alert: Alert) -> bool:
    role = user.role.name
    if role in ("compliance_auditor", "investigator", "team_lead", "admin"):
        return True
    if role == "analyst":
        return (
            alert.assignee_id == user.id
            or alert.status == AlertStatus.NEW.value
        )
    return False


def can_modify_alert(user: User, alert: Alert) -> bool:
    if is_terminal(alert):
        return False
    role = user.role.name
    if role in ("team_lead", "admin"):
        return True
    if role == "investigator":
        return True
    return False


def can_assign_alert(user: User, alert: Alert) -> bool:
    if is_terminal(alert):
        return False
    return user.role.name in ALERT_ASSIGN_ROLES and alert.status in (
        AlertStatus.NEW.value,
        AlertStatus.ASSIGNED.value,
    )


def can_escalate_alert(user: User, alert: Alert) -> bool:
    if is_terminal(alert):
        return False
    return user.role.name in ALERT_ESCALATE_ROLES and alert.status in (
        AlertStatus.NEW.value,
        AlertStatus.ASSIGNED.value,
    )


def can_resolve_alert(user: User, alert: Alert) -> bool:
    if is_terminal(alert):
        return False
    return user.role.name in ALERT_RESOLVE_ROLES


def can_delete_alert(user: User) -> bool:
    return user.role.name in ALERT_DELETE_ROLES


def enforce_view(user: User, alert: Alert) -> None:
    if not can_view_alert(user, alert):
        raise AuthorizationError("You do not have permission to view this alert")


def enforce_modify(user: User, alert: Alert) -> None:
    if not can_modify_alert(user, alert):
        raise AuthorizationError("You do not have permission to modify this alert")


def enforce_assign(user: User, alert: Alert) -> None:
    if not can_assign_alert(user, alert):
        raise AuthorizationError("You do not have permission to assign this alert")


def enforce_escalate(user: User, alert: Alert) -> None:
    if not can_escalate_alert(user, alert):
        raise AuthorizationError("You do not have permission to escalate this alert")


def enforce_resolve(user: User, alert: Alert) -> None:
    if not can_resolve_alert(user, alert):
        raise AuthorizationError("You do not have permission to resolve this alert")


def enforce_delete(user: User) -> None:
    if not can_delete_alert(user):
        raise AuthorizationError("You do not have permission to delete alerts")


def validate_transition(current: str, target: str) -> None:
    allowed = VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        from app.core.exceptions import ValidationConflictError

        raise ValidationConflictError(
            f"Cannot transition alert from {current!r} to {target!r}"
        )
