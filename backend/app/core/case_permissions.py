"""Case Management RBAC helpers (SEC-2).

Role matrix (simplified for v1):
- analyst: create + view/modify own cases, add notes
- investigator: analyst + close cases + view all cases
- team_lead: investigator + reassign any case
- compliance_auditor: read-only across all cases
- admin: full case operations
"""

from app.core.exceptions import AuthorizationError
from app.models.case import Case
from app.models.user import User

CASE_READ_ROLES = ("analyst", "investigator", "team_lead", "compliance_auditor", "admin")
CASE_CREATE_ROLES = ("analyst", "investigator", "team_lead", "admin")
CASE_NOTE_ROLES = ("analyst", "investigator", "team_lead", "admin")
CASE_STATUS_ROLES = ("analyst", "investigator", "team_lead", "admin")
CASE_ASSIGN_ROLES = ("analyst", "investigator", "team_lead", "admin")
CASE_CLOSE_ROLES = ("investigator", "team_lead", "admin")
CASE_REASSIGN_ROLES = ("team_lead", "admin")

CLOSED_STATUSES = frozenset({"closed_resolved", "closed_no_action"})


def is_closed(case: Case) -> bool:
    return case.status in CLOSED_STATUSES or case.status.startswith("closed")


def can_view_case(user: User, case: Case) -> bool:
    role = user.role.name
    if role in ("compliance_auditor", "investigator", "team_lead", "admin"):
        return True
    if role == "analyst":
        return case.owner_id == user.id
    return False


def can_modify_case(user: User, case: Case) -> bool:
    if is_closed(case):
        return False
    role = user.role.name
    if role in ("team_lead", "admin"):
        return True
    if role in ("investigator", "analyst"):
        return case.owner_id == user.id
    return False


def can_add_note(user: User, case: Case) -> bool:
    if is_closed(case):
        return False
    role = user.role.name
    if role in ("investigator", "team_lead", "admin"):
        return True
    if role == "analyst":
        return case.owner_id == user.id
    return False


def can_close_case(user: User, case: Case) -> bool:
    return user.role.name in CASE_CLOSE_ROLES and not is_closed(case)


def can_assign_case(user: User, case: Case) -> bool:
    if is_closed(case):
        return False
    role = user.role.name
    if role in ("team_lead", "admin"):
        return True
    if role in ("investigator", "analyst"):
        return case.owner_id is None or case.owner_id == user.id
    return False


def can_reassign_case(user: User) -> bool:
    return user.role.name in CASE_REASSIGN_ROLES


def enforce_view(user: User, case: Case) -> None:
    if not can_view_case(user, case):
        raise AuthorizationError("You do not have permission to view this case")


def enforce_modify(user: User, case: Case) -> None:
    if not can_modify_case(user, case):
        raise AuthorizationError("You do not have permission to modify this case")


def enforce_note(user: User, case: Case) -> None:
    if not can_add_note(user, case):
        raise AuthorizationError("You do not have permission to add notes to this case")


def enforce_close(user: User, case: Case) -> None:
    if not can_close_case(user, case):
        raise AuthorizationError("You do not have permission to close this case")


def enforce_assign(user: User, case: Case) -> None:
    if not can_assign_case(user, case):
        raise AuthorizationError("You do not have permission to assign this case")


def enforce_reassign(user: User) -> None:
    if not can_reassign_case(user):
        raise AuthorizationError("Only team leads and admins may reassign cases")
