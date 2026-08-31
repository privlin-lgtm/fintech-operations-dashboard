export type CaseStatus =
  | 'new'
  | 'in_progress'
  | 'pending_external'
  | 'escalated'
  | 'closed_resolved'
  | 'closed_no_action'

export type CasePriority = 'low' | 'medium' | 'high' | 'critical'
export type CaseType = 'dispute' | 'fraud' | 'aml_review'

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

export type CaseNote = {
  id: string
  case_id: string
  author_id: string
  body: string
  is_system: boolean
  created_at: string
  updated_at: string
}

export type CaseDetail = Case & {
  notes: CaseNote[]
}

export type CaseSearchParams = {
  status?: CaseStatus
  priority?: CasePriority
  assignee?: string
  sla_risk?: boolean
  limit?: number
  cursor?: string
}

export type CaseSearchFormValues = {
  status: '' | CaseStatus
  priority: '' | CasePriority
  assignee: string
  sla_risk: boolean
}

export const CASE_TYPE_OPTIONS = [
  { label: 'Dispute', value: 'dispute' as const },
  { label: 'Fraud', value: 'fraud' as const },
  { label: 'AML review', value: 'aml_review' as const },
]

export const CASE_STATUS_OPTIONS = [
  { label: 'New', value: 'new' as const },
  { label: 'In progress', value: 'in_progress' as const },
  { label: 'Pending external', value: 'pending_external' as const },
  { label: 'Escalated', value: 'escalated' as const },
  { label: 'Closed resolved', value: 'closed_resolved' as const },
  { label: 'Closed no action', value: 'closed_no_action' as const },
]

export const CASE_PRIORITY_OPTIONS = [
  { label: 'Low', value: 'low' as const },
  { label: 'Medium', value: 'medium' as const },
  { label: 'High', value: 'high' as const },
  { label: 'Critical', value: 'critical' as const },
]
