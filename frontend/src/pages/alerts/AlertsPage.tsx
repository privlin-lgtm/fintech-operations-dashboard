import { useCallback } from 'react'

import { Pagination } from '@/components/ui/Pagination'
import { AlertSearchForm } from '@/features/alerts/components/AlertSearchForm'
import { AlertTable } from '@/features/alerts/components/AlertTable'
import { ALERT_PAGE_SIZE, useAlertSearch } from '@/features/alerts/hooks/useAlertSearch'
import { setSearchParam, useCursorPagination } from '@/hooks/useCursorPagination'
import type { AlertSearchFormValues } from '@/types/alert'

export function AlertsPage() {
  const { data, isLoading, isError } = useAlertSearch()
  const { applySearchParams, goNext, goPrevious, hasPrevious, summary } =
    useCursorPagination('alert')

  const handleSearch = useCallback(
    (values: AlertSearchFormValues) => {
      const params = new URLSearchParams()
      setSearchParam(params, 'q', values.q.trim())
      setSearchParam(params, 'status', values.status)
      setSearchParam(params, 'severity', values.severity)
      setSearchParam(params, 'type', values.type)
      setSearchParam(params, 'sort', values.sort)
      applySearchParams(params)
    },
    [applySearchParams],
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Alert search</h1>
        <p className="mt-1 text-sm text-slate-500">
          Triage and filter alerts across the operations queue.
        </p>
      </div>

      <AlertSearchForm onSubmit={handleSearch} />

      <div className="space-y-0">
        <AlertTable alerts={data?.items ?? []} isLoading={isLoading} isError={isError} />
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

      <p className="text-xs text-slate-400">Page size: {ALERT_PAGE_SIZE} results per request.</p>
    </div>
  )
}
