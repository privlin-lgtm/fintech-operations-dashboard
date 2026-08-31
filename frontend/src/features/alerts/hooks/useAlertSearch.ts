import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'

import {
  fetchAlertDetail,
  parseAlertSearchParams,
  searchAlerts,
} from '@/features/alerts/alertsApi'

export const ALERT_PAGE_SIZE = 25

export function useAlertSearch() {
  const [searchParams] = useSearchParams()
  const filters = parseAlertSearchParams(searchParams)

  return useQuery({
    queryKey: ['alerts', 'search', filters],
    queryFn: () => searchAlerts(filters),
  })
}

export function useAlertDetail(alertId: string | undefined) {
  return useQuery({
    queryKey: ['alerts', 'detail', alertId],
    queryFn: () => fetchAlertDetail(alertId!),
    enabled: Boolean(alertId),
  })
}
