import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'

import {
  fetchCaseDetail,
  parseCaseSearchParams,
  searchCases,
} from '@/features/cases/casesApi'

export const CASE_PAGE_SIZE = 25

export function useCaseSearch() {
  const [searchParams] = useSearchParams()
  const filters = parseCaseSearchParams(searchParams)

  return useQuery({
    queryKey: ['cases', 'search', filters],
    queryFn: () => searchCases(filters),
  })
}

export function useCaseDetail(caseId: string | undefined) {
  return useQuery({
    queryKey: ['cases', 'detail', caseId],
    queryFn: () => fetchCaseDetail(caseId!),
    enabled: Boolean(caseId),
  })
}
