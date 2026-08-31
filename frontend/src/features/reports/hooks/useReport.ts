import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'

import {
  fetchAlertReport,
  fetchCaseReport,
  fetchSlaReport,
  fetchTransactionReport,
  parseReportSearchParams,
} from '@/features/reports/reportsApi'
import type { ReportType } from '@/types/report'
import { defaultGroupByForReport } from '@/types/report'

export function useReport(reportType: ReportType) {
  const [searchParams] = useSearchParams()
  const defaultGroupBy = defaultGroupByForReport(reportType)
  const filters = parseReportSearchParams(searchParams, defaultGroupBy)

  return useQuery({
    queryKey: ['reports', reportType, filters],
    queryFn: async () => {
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
    },
  })
}
