"""Who may see the assignable-users list, and who appears on it.

The list feeds the case Reassign and alert Assign pickers (team_lead/admin
and investigator/team_lead/admin) and the case search owner filter. That
filter also matters to compliance_auditor, who reads every case; an analyst
only ever sees their own cases, so the filter does nothing for them.
"""

from app.core.alert_permissions import ALERT_ASSIGN_ROLES
from app.core.case_permissions import CASE_REASSIGN_ROLES

ASSIGNABLE_USERS_READ_ROLES = tuple(
    dict.fromkeys((*CASE_REASSIGN_ROLES, *ALERT_ASSIGN_ROLES, "compliance_auditor"))
)

# Roles that can own a case or work an alert. compliance_auditor is read-only
# everywhere, so handing work to one would strand it.
ASSIGNABLE_ROLES = ("analyst", "investigator", "team_lead", "admin")
