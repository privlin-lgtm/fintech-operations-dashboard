import { useCallback } from 'react'

import { Pagination } from '@/components/ui/Pagination'
import { CaseSearchForm } from '@/features/cases/components/CaseSearchForm'
import { CaseTable } from '@/features/cases/components/CaseTable'
import { CASE_PAGE_SIZE, useCaseSearch } from '@/features/cases/hooks/useCaseSearch'
import { setSearchParam, useCursorPagination } from '@/hooks/useCursorPagination'
import type { CaseSearchFormValues } from '@/types/case'

export function CasesPage() {
  const { data, isLoading, isError } = useCaseSearch()
  const { applySearchParams, goNext, goPrevious, hasPrevious, summary } =
    useCursorPagination('case')

  const handleSearch = useCallback(
    (values: CaseSearchFormValues) => {
      const params = new URLSearchParams()
      setSearchParam(params, 'status', values.status)
      setSearchParam(params, 'priority', values.priority)
      setSearchParam(params, 'assignee', values.assignee.trim())
      setSearchParam(params, 'sla_risk', values.sla_risk ? 'true' : undefined)
      applySearchParams(params)
    },
    [applySearchParams],
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Case search</h1>
        <p className="mt-1 text-sm text-slate-500">
          Filter and review investigation cases across your queue.
        </p>
      </div>

      <CaseSearchForm onSubmit={handleSearch} />

      <div className="space-y-0">
        <CaseTable cases={data?.items ?? []} isLoading={isLoading} isError={isError} />
        {data && data.items.length > 0 ? (
          <Pagination
            summary={summary(data.items.length)}
            hasPrevious={hasPrevious}
            hasNext={Boolean(data.next_cursor)}
            onPrevious={goPrevious}
            onNext={() => goNext(data.next_cursor)}
          />
        ) : null}
      </div>

      <p className="text-xs text-slate-400">Page size: {CASE_PAGE_SIZE} results per request.</p>
    </div>
  )
}
