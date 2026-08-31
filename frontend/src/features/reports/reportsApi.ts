import { apiBlob, apiRequest } from '@/lib/api'
import { buildQueryString, dateInputToIso, dateInputToIsoEnd } from '@/lib/format'
import type {
  AlertVolumeReport,
  CaseVolumeReport,
  ExportFormat,
  ReportSchedule,
  ReportScheduleCreateInput,
  ReportSearchParams,
  ReportType,
  SlaPerformanceReport,
  TransactionVolumeReport,
} from '@/types/report'

function buildReportQuery(params: ReportSearchParams, format: ExportFormat = 'json') {
  return buildQueryString({
    from: params.from_date,
    to: params.to_date,
    group_by: params.group_by,
    format,
  })
}

export async function fetchTransactionReport(
  params: ReportSearchParams,
): Promise<TransactionVolumeReport> {
  return apiRequest<TransactionVolumeReport>(`/reports/transactions${buildReportQuery(params)}`)
}

export async function fetchCaseReport(params: ReportSearchParams): Promise<CaseVolumeReport> {
  return apiRequest<CaseVolumeReport>(`/reports/cases${buildReportQuery(params)}`)
}

export async function fetchAlertReport(params: ReportSearchParams): Promise<AlertVolumeReport> {
  return apiRequest<AlertVolumeReport>(`/reports/alerts${buildReportQuery(params)}`)
}

export async function fetchSlaReport(params: ReportSearchParams): Promise<SlaPerformanceReport> {
  return apiRequest<SlaPerformanceReport>(`/reports/sla${buildReportQuery(params)}`)
}

export async function downloadReport(
  reportType: ReportType,
  params: ReportSearchParams,
  format: 'csv' | 'pdf',
): Promise<void> {
  const blob = await apiBlob(`/reports/${reportType}${buildReportQuery(params, format)}`)
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${reportType}-report.${format}`
  anchor.click()
  URL.revokeObjectURL(url)
}

export async function createReportSchedule(data: ReportScheduleCreateInput): Promise<ReportSchedule> {
  return apiRequest<ReportSchedule>('/reports/schedules', { method: 'POST', body: data })
}

export function parseReportSearchParams(
  searchParams: URLSearchParams,
  defaultGroupBy: string,
): ReportSearchParams {
  const fromDate = searchParams.get('from_date')
  const toDate = searchParams.get('to_date')

  return {
    from_date: fromDate ? dateInputToIso(fromDate) : undefined,
    to_date: toDate ? dateInputToIsoEnd(toDate) : undefined,
    group_by: searchParams.get('group_by') ?? defaultGroupBy,
  }
}
