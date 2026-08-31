import { apiRequest } from '@/lib/api'
import { buildQueryString, parseEnumParam } from '@/lib/format'
import type { PaginatedResponse } from '@/types/api'
import { CASE_PRIORITY_OPTIONS, CASE_STATUS_OPTIONS } from '@/types/case'
import type { Case, CaseDetail, CaseSearchParams } from '@/types/case'

const STATUS_VALUES = CASE_STATUS_OPTIONS.map((option) => option.value)
const PRIORITY_VALUES = CASE_PRIORITY_OPTIONS.map((option) => option.value)

export type AddCaseNoteInput = {
  body: string
}

export type CloseCaseInput = {
  resolution_code: string
  closing_summary: string
  status: 'closed_resolved' | 'closed_no_action'
}

export type ReassignCaseInput = {
  owner_id: string
  reason: string
}

export async function searchCases(params: CaseSearchParams): Promise<PaginatedResponse<Case>> {
  const query = buildQueryString({
    status: params.status,
    priority: params.priority,
    assignee: params.assignee,
    sla_risk: params.sla_risk ? 'true' : undefined,
    limit: params.limit ?? 25,
    cursor: params.cursor,
  })

  return apiRequest<PaginatedResponse<Case>>(`/cases${query}`)
}

export async function fetchCaseDetail(caseId: string): Promise<CaseDetail> {
  return apiRequest<CaseDetail>(`/cases/${caseId}`)
}

export async function addCaseNote(caseId: string, data: AddCaseNoteInput): Promise<CaseDetail> {
  return apiRequest<CaseDetail>(`/cases/${caseId}/notes`, { method: 'POST', body: data })
}

export async function closeCase(caseId: string, data: CloseCaseInput): Promise<Case> {
  return apiRequest<Case>(`/cases/${caseId}/close`, { method: 'POST', body: data })
}

export async function reassignCase(caseId: string, data: ReassignCaseInput): Promise<Case> {
  return apiRequest<Case>(`/cases/${caseId}/reassign`, { method: 'POST', body: data })
}

export function parseCaseSearchParams(searchParams: URLSearchParams): CaseSearchParams {
  return {
    status: parseEnumParam(searchParams.get('status'), STATUS_VALUES),
    priority: parseEnumParam(searchParams.get('priority'), PRIORITY_VALUES),
    assignee: searchParams.get('assignee') ?? undefined,
    sla_risk: searchParams.get('sla_risk') === 'true' ? true : undefined,
    cursor: searchParams.get('cursor') ?? undefined,
    limit: 25,
  }
}
