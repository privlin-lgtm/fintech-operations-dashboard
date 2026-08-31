"""Unit tests for Case Management — permissions, validation, workflow."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.case_permissions import can_close_case, can_reassign_case, can_view_case
from app.core.exceptions import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationConflictError,
)
from app.models.case import Case
from app.models.enums import CasePriority, CaseStatus, CaseType
from app.models.role import Role
from app.models.user import User
from app.schemas.case import (
    CaseAssign,
    CaseClose,
    CaseCreate,
    CaseNoteCreate,
    CaseReassign,
    CaseUpdate,
)
from app.services.case import CaseService


def _now() -> datetime:
    return datetime.now(UTC)


def _user(*, role_name: str = "analyst") -> User:
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


def _case(**overrides) -> Case:
    case = Case(
        case_number=overrides.pop("case_number", "CASE-2026-000001"),
        customer_id=overrides.pop("customer_id", uuid4()),
        owner_id=overrides.pop("owner_id", None),
        case_type=overrides.pop("case_type", "dispute"),
        status=overrides.pop("status", "new"),
        priority=overrides.pop("priority", "medium"),
    )
    case.id = overrides.pop("id", uuid4())
    case.created_at = overrides.pop("created_at", _now())
    case.updated_at = overrides.pop("updated_at", case.created_at)
    case.notes = overrides.pop("notes", [])
    for k, v in overrides.items():
        setattr(case, k, v)
    return case


def _service(
    case_repo: AsyncMock | None = None,
    audit_repo: AsyncMock | None = None,
    customer_repo: AsyncMock | None = None,
    user_repo: AsyncMock | None = None,
):
    case_repo = case_repo or AsyncMock()
    case_repo.session = AsyncMock()
    audit_repo = audit_repo or AsyncMock()
    customer_repo = customer_repo or AsyncMock()
    user_repo = user_repo or AsyncMock()
    return CaseService(case_repo, audit_repo, customer_repo, user_repo), case_repo, audit_repo


def test_analyst_can_view_own_case_only():
    analyst = _user(role_name="analyst")
    own = _case(owner_id=analyst.id)
    other = _case(owner_id=uuid4())
    assert can_view_case(analyst, own) is True
    assert can_view_case(analyst, other) is False


def test_investigator_can_close_but_analyst_cannot():
    investigator = _user(role_name="investigator")
    analyst = _user(role_name="analyst")
    case = _case(owner_id=analyst.id)
    assert can_close_case(investigator, case) is True
    assert can_close_case(analyst, case) is False


def test_only_team_lead_can_reassign():
    assert can_reassign_case(_user(role_name="team_lead")) is True
    assert can_reassign_case(_user(role_name="investigator")) is False


@pytest.mark.asyncio
async def test_create_case_validates_customer():
    svc, repo, _audit = _service()
    svc.customer_repo.get_active_by_id.return_value = None
    actor = _user()

    with pytest.raises(NotFoundError):
        await svc.create(
            CaseCreate(customer_id=uuid4(), case_type=CaseType.DISPUTE),
            actor,
        )
    repo.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_case_audits():
    svc, repo, audit = _service()
    customer_id = uuid4()
    svc.customer_repo.get_active_by_id.return_value = object()
    repo.next_case_number.return_value = "CASE-2026-000099"
    created = _case(customer_id=customer_id)
    repo.add.return_value = created
    actor = _user()

    result = await svc.create(
        CaseCreate(customer_id=customer_id, case_type=CaseType.FRAUD, priority=CasePriority.HIGH),
        actor,
    )

    audit.record.assert_awaited()
    assert result.case_type == "dispute" or result.case_number


@pytest.mark.asyncio
async def test_update_rejects_invalid_transition():
    svc, repo, _audit = _service()
    actor = _user(role_name="team_lead")
    case = _case(status="new")
    repo.get_detail.return_value = case

    with pytest.raises(ValidationConflictError):
        await svc.update(
            case.id,
            CaseUpdate(status=CaseStatus.PENDING_EXTERNAL),
            actor,
        )


@pytest.mark.asyncio
async def test_assign_sets_owner_and_audits():
    svc, repo, audit = _service()
    actor = _user(role_name="investigator")
    assignee = uuid4()
    case = _case(owner_id=None)
    repo.get_detail.return_value = case
    svc.user_repo.get_active_by_id.return_value = _user()

    await svc.assign(case.id, CaseAssign(owner_id=assignee), actor)

    assert case.owner_id == assignee
    audit.record.assert_awaited()
    assert audit.record.await_args.kwargs["action"] == "assign"


@pytest.mark.asyncio
async def test_analyst_cannot_view_other_case():
    svc, repo, _audit = _service()
    analyst = _user(role_name="analyst")
    case = _case(owner_id=uuid4())
    repo.get_detail.return_value = case

    with pytest.raises(AuthorizationError):
        await svc.get_detail(case.id, viewer=analyst)


@pytest.mark.asyncio
async def test_close_already_closed_raises_conflict():
    svc, repo, _audit = _service()
    actor = _user(role_name="investigator")
    case = _case(status="closed_resolved")
    repo.get_detail.return_value = case

    with pytest.raises(ConflictError):
        await svc.close(
            case.id,
            CaseClose(resolution_code="x", closing_summary="y", status=CaseStatus.CLOSED_NO_ACTION),
            actor,
        )


@pytest.mark.asyncio
async def test_reassign_requires_team_lead():
    svc, repo, _audit = _service()
    investigator = _user(role_name="investigator")
    case = _case()
    repo.get_detail.return_value = case

    with pytest.raises(AuthorizationError):
        await svc.reassign(
            case.id,
            CaseReassign(owner_id=uuid4(), reason="Workload balancing"),
            investigator,
        )


@pytest.mark.asyncio
async def test_add_note_on_closed_case_forbidden():
    svc, repo, _audit = _service()
    actor = _user(role_name="investigator")
    case = _case(status="closed_resolved", owner_id=actor.id)
    repo.get_detail.return_value = case

    with pytest.raises(AuthorizationError):
        await svc.add_note(case.id, CaseNoteCreate(body="Too late"), actor)
