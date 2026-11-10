export type Role = {
  id: string
  name: string
  description: string | null
  permissions: Record<string, unknown>
  created_at: string
  updated_at: string
}

export type User = {
  id: string
  email: string
  full_name: string
  role_id: string
  mfa_enabled: boolean
  status: string
  last_login_at: string | null
  created_at: string
  updated_at: string
  role: Role | null
}

/** A person a case or alert can be handed to (GET /users/assignable). */
export type AssignableUser = {
  id: string
  full_name: string
  role: string
}

export type DashboardSummary = {
  open_cases: number
  sla_at_risk: number
  new_alerts: number
  cases_closed_today: number
}
