// Mirrors the backend's require_roles(...) tuples exactly (see
// backend/app/api/v1/endpoints/*.py). When a route's allowed roles change on
// the backend, this map changes in the same PR — it is the one place the
// frontend claims to know who can do what, and it's a claim, not a guarantee:
// the backend enforces this for real, this file only decides what to show.
export const PERMISSIONS = {
  'customer:read': ['analyst', 'investigator', 'team_lead', 'compliance_auditor', 'admin'],
  'customer:write': ['admin', 'team_lead'],
  // Case note/close/reassign and alert dismiss/escalate currently require only
  // authentication on the backend (get_current_user, no require_roles) — every
  // role is listed here to match that, not as an aspirational restriction.
  'case:read': ['analyst', 'investigator', 'team_lead', 'compliance_auditor', 'admin'],
  'case:write': ['analyst', 'investigator', 'team_lead', 'compliance_auditor', 'admin'],
  'alert:read': ['analyst', 'investigator', 'team_lead', 'compliance_auditor', 'admin'],
  'alert:write': ['analyst', 'investigator', 'team_lead', 'compliance_auditor', 'admin'],
  'report:read': ['analyst', 'investigator', 'team_lead', 'compliance_auditor', 'admin'],
  'report:schedule': ['team_lead', 'compliance_auditor', 'admin'],
} as const satisfies Record<string, readonly string[]>

export type Permission = keyof typeof PERMISSIONS

export function roleHasPermission(roleName: string | null | undefined, permission: Permission): boolean {
  if (!roleName) {
    return false
  }
  return (PERMISSIONS[permission] as readonly string[]).includes(roleName)
}
