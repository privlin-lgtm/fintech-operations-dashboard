export type ExportFormat = 'json' | 'csv' | 'pdf'

export type ReportType = 'transactions' | 'cases' | 'alerts' | 'sla'

export type VolumeRow = {
  group: string
  count: number
}

export type TransactionVolumeRow = VolumeRow & {
  total_amount_cents: number
}

export type TransactionVolumeReport = {
  report_type: string
  group_by: string
  rows: TransactionVolumeRow[]
  total_count: number
  total_amount_cents: number
}

export type CaseVolumeReport = {
  report_type: string
  group_by: string
  rows: VolumeRow[]
  total_count: number
}

export type AlertVolumeReport = {
  report_type: string
  group_by: string
  rows: VolumeRow[]
  total_count: number
}

export type SlaBreakdownRow = {
  group: string
  closed: number
  met_sla: number
  missed_sla: number
}

export type SlaPerformanceReport = {
  report_type: string
  group_by: string
  total_closed: number
  met_sla: number
  missed_sla: number
  currently_at_risk: number
  compliance_rate: number | null
  breakdown: SlaBreakdownRow[]
}

export type ReportCadence = 'once' | 'daily' | 'weekly' | 'monthly'

export type ReportSchedule = {
  id: string
  report_type: string
  filters: Record<string, unknown>
  cadence: ReportCadence | null
  recipients: string[]
  created_by: string
  last_run_at: string | null
  next_run_at: string | null
  created_at: string
  updated_at: string
}

export type ReportScheduleCreateInput = {
  report_type: ReportType
  filters?: Record<string, unknown>
  cadence: ReportCadence
  recipients: string[]
}

export type ReportScheduleFormValues = {
  cadence: ReportCadence
  recipients: string
}

export const REPORT_CADENCE_OPTIONS: { label: string; value: ReportCadence }[] = [
  { label: 'Daily', value: 'daily' },
  { label: 'Weekly', value: 'weekly' },
  { label: 'Monthly', value: 'monthly' },
]

export type ReportSearchParams = {
  from_date?: string
  to_date?: string
  group_by?: string
  format?: ExportFormat
}

export type ReportSearchFormValues = {
  from_date: string
  to_date: string
  group_by: string
}

export const REPORT_TYPE_OPTIONS: { label: string; value: ReportType; description: string }[] = [
  {
    label: 'Daily transactions',
    value: 'transactions',
    description: 'Transaction volume and value aggregated over time.',
  },
  {
    label: 'Case volume',
    value: 'cases',
    description: 'Case counts grouped by status, priority, or type.',
  },
  {
    label: 'Alert volume',
    value: 'alerts',
    description: 'Alert disposition and severity breakdowns.',
  },
  {
    label: 'SLA performance',
    value: 'sla',
    description: 'SLA compliance metrics and breach analysis.',
  },
]

export const TRANSACTION_REPORT_GROUP_OPTIONS = [
  { label: 'Day', value: 'day' },
  { label: 'Status', value: 'status' },
  { label: 'Channel', value: 'channel' },
  { label: 'Direction', value: 'direction' },
]

export const CASE_REPORT_GROUP_OPTIONS = [
  { label: 'Status', value: 'status' },
  { label: 'Priority', value: 'priority' },
  { label: 'Case type', value: 'case_type' },
  { label: 'Day', value: 'day' },
]

export const ALERT_REPORT_GROUP_OPTIONS = [
  { label: 'Status', value: 'status' },
  { label: 'Severity', value: 'severity' },
  { label: 'Alert type', value: 'alert_type' },
  { label: 'Day', value: 'day' },
]

export const SLA_REPORT_GROUP_OPTIONS = [
  { label: 'Priority', value: 'priority' },
  { label: 'Case type', value: 'case_type' },
]

export function groupOptionsForReport(type: ReportType) {
  switch (type) {
    case 'transactions':
      return TRANSACTION_REPORT_GROUP_OPTIONS
    case 'cases':
      return CASE_REPORT_GROUP_OPTIONS
    case 'alerts':
      return ALERT_REPORT_GROUP_OPTIONS
    case 'sla':
      return SLA_REPORT_GROUP_OPTIONS
  }
}

export function defaultGroupByForReport(type: ReportType): string {
  switch (type) {
    case 'transactions':
      return 'day'
    case 'cases':
      return 'status'
    case 'alerts':
      return 'status'
    case 'sla':
      return 'priority'
  }
}
