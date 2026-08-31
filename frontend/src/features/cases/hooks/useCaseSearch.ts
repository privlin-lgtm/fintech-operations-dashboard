import { skipToken, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'

import type { AddCaseNoteInput, CloseCaseInput, CreateCaseInput, ReassignCaseInput } from '@/features/cases/casesApi'
import {
  addCaseNote,
  closeCase,
  createCase,
  fetchCaseDetail,
  parseCaseSearchParams,
  reassignCase,
  searchCases,
} from '@/features/cases/casesApi'
import { caseKeys } from '@/lib/queryKeys'

export const CASE_PAGE_SIZE = 25

export function useCaseSearch() {
  const [searchParams] = useSearchParams()
  const filters = parseCaseSearchParams(searchParams)

  return useQuery({
    queryKey: caseKeys.list(filters),
    queryFn: () => searchCases(filters),
  })
}

export function useCaseDetail(caseId: string | undefined) {
  return useQuery({
    queryKey: caseKeys.detail(caseId ?? ''),
    queryFn: caseId ? () => fetchCaseDetail(caseId) : skipToken,
  })
}

function useInvalidateCase(caseId: string) {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: caseKeys.detail(caseId) })
    void queryClient.invalidateQueries({ queryKey: caseKeys.lists() })
  }
}

// No onMutate/optimistic update on any of these three: a case action can
// still be rejected by the backend (e.g. closing without a resolution code),
// so the UI waits for the real answer instead of showing one that might not
// have happened.

export function useCreateCase() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateCaseInput) => createCase(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: caseKeys.lists() })
    },
  })
}

export function useAddCaseNote(caseId: string) {
  const invalidate = useInvalidateCase(caseId)
  return useMutation({
    mutationFn: (data: AddCaseNoteInput) => addCaseNote(caseId, data),
    onSuccess: invalidate,
  })
}

export function useCloseCase(caseId: string) {
  const invalidate = useInvalidateCase(caseId)
  return useMutation({
    mutationFn: (data: CloseCaseInput) => closeCase(caseId, data),
    onSuccess: invalidate,
  })
}

export function useReassignCase(caseId: string) {
  const invalidate = useInvalidateCase(caseId)
  return useMutation({
    mutationFn: (data: ReassignCaseInput) => reassignCase(caseId, data),
    onSuccess: invalidate,
  })
}
