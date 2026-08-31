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
