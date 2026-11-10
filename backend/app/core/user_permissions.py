"""Who may see the assignable-users list, and who appears on it.

The list feeds the case Reassign and alert Assign pickers, so it is open to
exactly the roles that can use one of those forms (team_lead/admin for case
reassignment, investigator/team_lead/admin for alert assignment).
"""

from app.core.alert_permissions import ALERT_ASSIGN_ROLES
from app.core.case_permissions import CASE_REASSIGN_ROLES

ASSIGNABLE_USERS_READ_ROLES = tuple(dict.fromkeys((*CASE_REASSIGN_ROLES, *ALERT_ASSIGN_ROLES)))

# Roles that can own a case or work an alert. compliance_auditor is read-only
# everywhere, so handing work to one would strand it.
ASSIGNABLE_ROLES = ("analyst", "investigator", "team_lead", "admin")
