export type Case = {
  id: string
  case_number: string
  customer_id: string
  owner_id: string | null
  case_type: string
  status: string
  priority: string
  sla_due_at: string | null
  resolution_code: string | null
  closing_summary: string | null
  closed_at: string | null
  created_at: string
  updated_at: string
}
