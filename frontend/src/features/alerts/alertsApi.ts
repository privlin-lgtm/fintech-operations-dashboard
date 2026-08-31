import { apiRequest } from '@/lib/api'
import { buildQueryString } from '@/lib/format'
import { getAccessToken } from '@/lib/storage'
import type { PaginatedResponse } from '@/types/api'
import type { Alert, AlertSearchParams } from '@/types/alert'

function authHeaders() {
  return { token: getAccessToken() }
}

export async function searchAlerts(params: AlertSearchParams): Promise<PaginatedResponse<Alert>> {
  const query = buildQueryString({
    q: params.q,
    customer_id: params.customer_id,
    assignee_id: params.assignee_id,
    severity: params.severity,
    status: params.status,
    type: params.alert_type,
    sort: params.sort ?? '-created_at',
    limit: params.limit ?? 25,
    cursor: params.cursor,
  })

  return apiRequest<PaginatedResponse<Alert>>(`/alerts${query}`, authHeaders())
}

export async function fetchAlertDetail(alertId: string): Promise<Alert> {
  return apiRequest<Alert>(`/alerts/${alertId}`, authHeaders())
}

export function parseAlertSearchParams(searchParams: URLSearchParams): AlertSearchParams {
  return {
    q: searchParams.get('q') ?? undefined,
    status: (searchParams.get('status') as AlertSearchParams['status']) ?? undefined,
    severity: (searchParams.get('severity') as AlertSearchParams['severity']) ?? undefined,
    alert_type: (searchParams.get('type') as AlertSearchParams['alert_type']) ?? undefined,
    sort: (searchParams.get('sort') as AlertSearchParams['sort']) ?? '-created_at',
    cursor: searchParams.get('cursor') ?? undefined,
    limit: 25,
  }
}
