import { skipToken, useMutation, useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'

import {
  createReportSchedule,
  fetchAlertReport,
  fetchCaseReport,
  fetchSlaReport,
  fetchTransactionReport,
  parseReportSearchParams,
} from '@/features/reports/reportsApi'
import { reportKeys } from '@/lib/queryKeys'
import type {
  AlertVolumeReport,
  CaseVolumeReport,
  ReportScheduleCreateInput,
  ReportType,
  SlaPerformanceReport,
  TransactionVolumeReport,
} from '@/types/report'
import { defaultGroupByForReport } from '@/types/report'

function fetchReport(
  reportType: ReportType,
  filters: ReturnType<typeof parseReportSearchParams>,
): Promise<TransactionVolumeReport | CaseVolumeReport | AlertVolumeReport | SlaPerformanceReport> {
  switch (reportType) {
    case 'transactions':
      return fetchTransactionReport(filters)
    case 'cases':
      return fetchCaseReport(filters)
    case 'alerts':
      return fetchAlertReport(filters)
    case 'sla':
      return fetchSlaReport(filters)
  }
}

/** `reportType` is undefined for an invalid :reportType route param — the
 * query is skipped rather than the hook being called conditionally, so
 * hook order stays the same across every render. */
export function useReport(reportType: ReportType | undefined) {
  const [searchParams] = useSearchParams()
  const defaultGroupBy = reportType ? defaultGroupByForReport(reportType) : ''
  const filters = parseReportSearchParams(searchParams, defaultGroupBy)

  return useQuery({
    queryKey: reportKeys.detail(reportType ?? '', filters),
    queryFn: reportType ? () => fetchReport(reportType, filters) : skipToken,
  })
}

export function useCreateReportSchedule() {
  return useMutation({
    mutationFn: (data: ReportScheduleCreateInput) => createReportSchedule(data),
  })
}
