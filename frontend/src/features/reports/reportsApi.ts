import { getAccessToken } from '@/lib/storage'
import { buildQueryString, dateInputToIso, dateInputToIsoEnd } from '@/lib/format'
import type {
  AlertVolumeReport,
  CaseVolumeReport,
  ExportFormat,
  ReportSearchParams,
  ReportType,
  SlaPerformanceReport,
  TransactionVolumeReport,
} from '@/types/report'

const API_BASE = import.meta.env.VITE_API_URL ?? '/api/v1'

function authHeaders(): Record<string, string> {
  const token = getAccessToken()
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  return headers
}

function buildReportQuery(params: ReportSearchParams, format: ExportFormat = 'json') {
  return buildQueryString({
    from: params.from_date,
    to: params.to_date,
    group_by: params.group_by,
    format,
  })
}

async function fetchReport<T>(path: string, params: ReportSearchParams): Promise<T> {
  const response = await fetch(`${API_BASE}${path}${buildReportQuery(params)}`, {
    headers: authHeaders(),
  })

  if (!response.ok) {
    throw new Error('Failed to load report')
  }

  return (await response.json()) as T
}

export async function fetchTransactionReport(
  params: ReportSearchParams,
): Promise<TransactionVolumeReport> {
  return fetchReport<TransactionVolumeReport>('/reports/transactions', params)
}

export async function fetchCaseReport(params: ReportSearchParams): Promise<CaseVolumeReport> {
  return fetchReport<CaseVolumeReport>('/reports/cases', params)
}

export async function fetchAlertReport(params: ReportSearchParams): Promise<AlertVolumeReport> {
  return fetchReport<AlertVolumeReport>('/reports/alerts', params)
}

export async function fetchSlaReport(params: ReportSearchParams): Promise<SlaPerformanceReport> {
  return fetchReport<SlaPerformanceReport>('/reports/sla', params)
}

export async function downloadReport(
  reportType: ReportType,
  params: ReportSearchParams,
  format: 'csv' | 'pdf',
): Promise<void> {
  const response = await fetch(
    `${API_BASE}/reports/${reportType}${buildReportQuery(params, format)}`,
    { headers: authHeaders() },
  )

  if (!response.ok) {
    throw new Error('Failed to download report')
  }

  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${reportType}-report.${format}`
  anchor.click()
  URL.revokeObjectURL(url)
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
