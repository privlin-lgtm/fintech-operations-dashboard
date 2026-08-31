import { skipToken, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'

import type { DismissAlertInput, EscalateAlertInput } from '@/features/alerts/alertsApi'
import {
  dismissAlert,
  escalateAlert,
  fetchAlertDetail,
  parseAlertSearchParams,
  searchAlerts,
} from '@/features/alerts/alertsApi'
import { alertKeys, caseKeys } from '@/lib/queryKeys'

export const ALERT_PAGE_SIZE = 25

export function useAlertSearch() {
  const [searchParams] = useSearchParams()
  const filters = parseAlertSearchParams(searchParams)

  return useQuery({
    queryKey: alertKeys.list(filters),
    queryFn: () => searchAlerts(filters),
  })
}

export function useAlertDetail(alertId: string | undefined) {
  return useQuery({
    queryKey: alertKeys.detail(alertId ?? ''),
    queryFn: alertId ? () => fetchAlertDetail(alertId) : skipToken,
  })
}

function useInvalidateAlert(alertId: string) {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: alertKeys.detail(alertId) })
    void queryClient.invalidateQueries({ queryKey: alertKeys.lists() })
  }
}

export function useDismissAlert(alertId: string) {
  const invalidate = useInvalidateAlert(alertId)
  return useMutation({
    mutationFn: (data: DismissAlertInput) => dismissAlert(alertId, data),
    onSuccess: invalidate,
  })
}

export function useEscalateAlert(alertId: string) {
  const invalidate = useInvalidateAlert(alertId)
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: EscalateAlertInput) => escalateAlert(alertId, data),
    onSuccess: () => {
      invalidate()
      // Escalating either links an existing case or creates one — either way
      // the case queue/detail the alert now points at is stale.
      void queryClient.invalidateQueries({ queryKey: caseKeys.lists() })
    },
  })
}
