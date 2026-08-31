export type AlertStatus = 'new' | 'assigned' | 'escalated' | 'resolved'
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical'
export type AlertType =
  | 'high_risk_txn'
  | 'velocity'
  | 'sanctions_match'
  | 'login_anomaly'
  | 'manual_watchlist'

export type AlertSortField =
  | 'created_at'
  | '-created_at'
  | 'severity'
  | '-severity'
  | 'status'
  | '-status'

export type Alert = {
  id: string
  customer_id: string
  transaction_id: string | null
  case_id: string | null
  assignee_id: string | null
  alert_type: string
  severity: string
  status: string
  triggering_reason: string
  dismissal_reason: string | null
  resolved_at: string | null
  created_at: string
  updated_at: string
}

export type AlertSearchParams = {
  q?: string
  customer_id?: string
  assignee_id?: string
  severity?: AlertSeverity
  status?: AlertStatus
  alert_type?: AlertType
  sort?: AlertSortField
  limit?: number
  cursor?: string
}

export type AlertSearchFormValues = {
  q: string
  status: '' | AlertStatus
  severity: '' | AlertSeverity
  type: '' | AlertType
  sort: AlertSortField
}

export const ALERT_STATUS_OPTIONS = [
  { label: 'New', value: 'new' as const },
  { label: 'Assigned', value: 'assigned' as const },
  { label: 'Escalated', value: 'escalated' as const },
  { label: 'Resolved', value: 'resolved' as const },
]

export const ALERT_SEVERITY_OPTIONS = [
  { label: 'Low', value: 'low' as const },
  { label: 'Medium', value: 'medium' as const },
  { label: 'High', value: 'high' as const },
  { label: 'Critical', value: 'critical' as const },
]

export const ALERT_TYPE_OPTIONS = [
  { label: 'High risk txn', value: 'high_risk_txn' as const },
  { label: 'Velocity', value: 'velocity' as const },
  { label: 'Sanctions match', value: 'sanctions_match' as const },
  { label: 'Login anomaly', value: 'login_anomaly' as const },
  { label: 'Manual watchlist', value: 'manual_watchlist' as const },
]

export const ALERT_SORT_OPTIONS = [
  { label: 'Newest first', value: '-created_at' as const },
  { label: 'Oldest first', value: 'created_at' as const },
  { label: 'Severity high–low', value: '-severity' as const },
  { label: 'Status', value: 'status' as const },
]
