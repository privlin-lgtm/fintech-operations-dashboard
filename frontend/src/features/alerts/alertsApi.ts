import { apiRequest } from '@/lib/api'
import { buildQueryString, parseEnumParam } from '@/lib/format'
import type { PaginatedResponse } from '@/types/api'
import {
  ALERT_SEVERITY_OPTIONS,
  ALERT_SORT_OPTIONS,
  ALERT_STATUS_OPTIONS,
  ALERT_TYPE_OPTIONS,
} from '@/types/alert'
import type { Alert, AlertSearchParams } from '@/types/alert'
import type { CasePriority, CaseType } from '@/types/case'

const STATUS_VALUES = ALERT_STATUS_OPTIONS.map((option) => option.value)
const SEVERITY_VALUES = ALERT_SEVERITY_OPTIONS.map((option) => option.value)
const TYPE_VALUES = ALERT_TYPE_OPTIONS.map((option) => option.value)
const SORT_VALUES = ALERT_SORT_OPTIONS.map((option) => option.value)

export type DismissAlertInput = {
  reason: string
}

export type EscalateAlertInput =
  | { case_id: string; create_case?: false }
  | { create_case: true; case_type: CaseType; priority: CasePriority }

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

  return apiRequest<PaginatedResponse<Alert>>(`/alerts${query}`)
}

export async function fetchAlertDetail(alertId: string): Promise<Alert> {
  return apiRequest<Alert>(`/alerts/${alertId}`)
}

export async function dismissAlert(alertId: string, data: DismissAlertInput): Promise<Alert> {
  return apiRequest<Alert>(`/alerts/${alertId}/dismiss`, { method: 'POST', body: data })
}

export async function escalateAlert(alertId: string, data: EscalateAlertInput): Promise<Alert> {
  return apiRequest<Alert>(`/alerts/${alertId}/escalate`, { method: 'POST', body: data })
}

export function parseAlertSearchParams(searchParams: URLSearchParams): AlertSearchParams {
  return {
    q: searchParams.get('q') ?? undefined,
    status: parseEnumParam(searchParams.get('status'), STATUS_VALUES),
    severity: parseEnumParam(searchParams.get('severity'), SEVERITY_VALUES),
    alert_type: parseEnumParam(searchParams.get('type'), TYPE_VALUES),
    sort: parseEnumParam(searchParams.get('sort'), SORT_VALUES) ?? '-created_at',
    cursor: searchParams.get('cursor') ?? undefined,
    limit: 25,
  }
}
