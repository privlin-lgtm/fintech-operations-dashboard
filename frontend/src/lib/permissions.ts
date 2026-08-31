// Mirrors the backend's require_roles(...) tuples exactly (see
// backend/app/api/v1/endpoints/*.py and the *_ROLES tuples in
// core/case_permissions.py / core/alert_permissions.py). When a route's
// allowed roles change on the backend, this map changes in the same PR — it
// is the one place the frontend claims to know who can do what, and it's a
// claim, not a guarantee: the backend enforces this for real, this file only
// decides what to show.
export const PERMISSIONS = {
  'customer:read': ['analyst', 'investigator', 'team_lead', 'compliance_auditor', 'admin'],
  'customer:write': ['admin', 'team_lead'],
  'case:read': ['analyst', 'investigator', 'team_lead', 'compliance_auditor', 'admin'],
  'case:create': ['analyst', 'investigator', 'team_lead', 'admin'],
  'case:note': ['analyst', 'investigator', 'team_lead', 'admin'],
  'case:close': ['investigator', 'team_lead', 'admin'],
  'case:reassign': ['team_lead', 'admin'],
  'alert:read': ['analyst', 'investigator', 'team_lead', 'compliance_auditor', 'admin'],
  'alert:assign': ['investigator', 'team_lead', 'admin'],
  'alert:escalate': ['investigator', 'team_lead', 'admin'],
  'alert:resolve': ['investigator', 'team_lead', 'admin'],
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
