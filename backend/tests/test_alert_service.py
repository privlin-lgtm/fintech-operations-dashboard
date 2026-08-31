"""Unit tests for Alert Management — permissions, workflow, validation."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.alert_permissions import (
    can_assign_alert,
    can_resolve_alert,
    can_view_alert,
    validate_transition,
)
from app.core.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationConflictError
from app.models.alert import Alert
from app.models.enums import AlertSeverity, AlertStatus, AlertType
from app.models.role import Role
from app.models.user import User
from app.schemas.alert import AlertAssign, AlertCreate, AlertResolve
from app.services.alert import AlertService


def _now() -> datetime:
    return datetime.now(UTC)


def _user(*, role_name: str = "investigator") -> User:
    role = Role(name=role_name, permissions={})
    role.id = uuid4()
    user = User(
        role_id=role.id,
        email=f"{role_name}@example.com",
        full_name="Test User",
        hashed_password="x",
    )
    user.id = uuid4()
    user.role = role
    return user


def _alert(**overrides) -> Alert:
    alert = Alert(
        customer_id=overrides.pop("customer_id", uuid4()),
        alert_type=overrides.pop("alert_type", "high_risk_txn"),
        severity=overrides.pop("severity", "high"),
        status=overrides.pop("status", "new"),
        triggering_reason=overrides.pop("triggering_reason", "Large transaction"),
    )
    alert.id = overrides.pop("id", uuid4())
    alert.created_at = overrides.pop("created_at", _now())
    alert.updated_at = overrides.pop("updated_at", alert.created_at)
    alert.assignee_id = overrides.pop("assignee_id", None)
    alert.case_id = overrides.pop("case_id", None)
    for k, v in overrides.items():
        setattr(alert, k, v)
    return alert


def _service():
    alert_repo = AsyncMock()
    alert_repo.session = AsyncMock()
    case_repo = AsyncMock()
    audit_repo = AsyncMock()
    customer_repo = AsyncMock()
    user_repo = AsyncMock()
    return (
        AlertService(alert_repo, case_repo, audit_repo, customer_repo, user_repo),
        alert_repo,
        audit_repo,
        customer_repo,
        user_repo,
    )


def test_validate_transition_new_to_assigned():
    validate_transition("new", "assigned")


def test_validate_transition_escalated_to_new_fails():
    with pytest.raises(ValidationConflictError):
        validate_transition("escalated", "new")


def test_analyst_can_view_new_queue_and_assigned():
    analyst = _user(role_name="analyst")
    assert can_view_alert(analyst, _alert(status="new")) is True
    assert can_view_alert(analyst, _alert(status="assigned", assignee_id=analyst.id)) is True
    assert can_view_alert(analyst, _alert(status="assigned", assignee_id=uuid4())) is False


def test_investigator_can_assign_new_alert():
    investigator = _user(role_name="investigator")
    assert can_assign_alert(investigator, _alert(status="new")) is True


@pytest.mark.asyncio
async def test_create_alert_validates_customer():
    svc, repo, _audit, customer_repo, _user_repo = _service()
    customer_repo.get_active_by_id.return_value = None
    with pytest.raises(NotFoundError):
        await svc.create(
            AlertCreate(
                customer_id=uuid4(),
                alert_type=AlertType.VELOCITY,
                severity=AlertSeverity.MEDIUM,
                triggering_reason="Velocity breach",
            ),
            _user(),
        )
    repo.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_transitions_to_assigned():
    svc, repo, audit, _customer_repo, user_repo = _service()
    investigator = _user(role_name="investigator")
    assignee = uuid4()
    alert = _alert(status="new")
    repo.get_active_by_id.return_value = alert
    user_repo.get_active_by_id.return_value = _user()

    result = await svc.assign(alert.id, AlertAssign(assignee_id=assignee), investigator)

    assert alert.status == "assigned"
    assert alert.assignee_id == assignee
    audit.record.assert_awaited()
    assert result.status == "assigned"


@pytest.mark.asyncio
async def test_resolve_sets_terminal_state():
    svc, repo, audit, _customer_repo, _user_repo = _service()
    investigator = _user(role_name="investigator")
    alert = _alert(status="assigned", assignee_id=investigator.id)
    repo.get_active_by_id.return_value = alert

    result = await svc.resolve(
        alert.id, AlertResolve(reason="False positive after review"), investigator
    )

    assert alert.status == "resolved"
    assert alert.dismissal_reason == "False positive after review"
    assert alert.resolved_at is not None
    assert result.status == "resolved"


@pytest.mark.asyncio
async def test_resolve_already_resolved_conflict():
    svc, repo, _audit, _customer_repo, _user_repo = _service()
    investigator = _user(role_name="investigator")
    alert = _alert(status="resolved")
    repo.get_active_by_id.return_value = alert

    with pytest.raises(ConflictError):
        await svc.resolve(alert.id, AlertResolve(reason="Too late"), investigator)


@pytest.mark.asyncio
async def test_analyst_cannot_view_other_assigned_alert():
    svc, repo, _audit, _customer_repo, _user_repo = _service()
    analyst = _user(role_name="analyst")
    alert = _alert(status="assigned", assignee_id=uuid4())
    repo.get_active_by_id.return_value = alert

    with pytest.raises(AuthorizationError):
        await svc.get_by_id(alert.id, viewer=analyst)
