import { apiRequest } from '@/lib/api'
import { buildQueryString } from '@/lib/format'
import { getAccessToken } from '@/lib/storage'
import type { PaginatedResponse } from '@/types/api'
import type { Case, CaseDetail, CaseSearchParams } from '@/types/case'

function authHeaders() {
  return { token: getAccessToken() }
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

  return apiRequest<PaginatedResponse<Case>>(`/cases${query}`, authHeaders())
}

export async function fetchCaseDetail(caseId: string): Promise<CaseDetail> {
  return apiRequest<CaseDetail>(`/cases/${caseId}`, authHeaders())
}

export function parseCaseSearchParams(searchParams: URLSearchParams): CaseSearchParams {
  return {
    status: (searchParams.get('status') as CaseSearchParams['status']) ?? undefined,
    priority: (searchParams.get('priority') as CaseSearchParams['priority']) ?? undefined,
    assignee: searchParams.get('assignee') ?? undefined,
    sla_risk: searchParams.get('sla_risk') === 'true' ? true : undefined,
    cursor: searchParams.get('cursor') ?? undefined,
    limit: 25,
  }
}
