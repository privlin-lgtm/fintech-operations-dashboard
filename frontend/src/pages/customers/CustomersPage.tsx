import { useCallback, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { Pagination } from '@/components/ui/Pagination'
import { CustomerSearchForm } from '@/features/customers/components/CustomerSearchForm'
import { CustomerTable } from '@/features/customers/components/CustomerTable'
import { PAGE_SIZE, useCustomerSearch } from '@/features/customers/hooks/useCustomerSearch'
import type { CustomerSearchFormValues } from '@/types/customer'

function applyFormValues(
  values: CustomerSearchFormValues,
  setSearchParams: ReturnType<typeof useSearchParams>[1],
) {
  const params = new URLSearchParams()

  if (values.q.trim()) {
    params.set('q', values.q.trim())
  }
  if (values.status) {
    params.set('status', values.status)
  }
  if (values.risk_tier) {
    params.set('risk_tier', values.risk_tier)
  }
  if (values.kyc_status) {
    params.set('kyc_status', values.kyc_status)
  }
  if (values.sort) {
    params.set('sort', values.sort)
  }

  setSearchParams(params)
}

export function CustomersPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [cursorHistory, setCursorHistory] = useState<string[]>([])
  const { data, isLoading, isError } = useCustomerSearch()

  const currentCursor = searchParams.get('cursor')

  const handleSearch = useCallback(
    (values: CustomerSearchFormValues) => {
      setCursorHistory([])
      applyFormValues(values, setSearchParams)
    },
    [setSearchParams],
  )

  const handleNext = useCallback(() => {
    if (!data?.next_cursor) {
      return
    }

    setCursorHistory((history) => [...history, currentCursor ?? ''])
    const params = new URLSearchParams(searchParams)
    params.set('cursor', data.next_cursor)
    setSearchParams(params)
  }, [currentCursor, data?.next_cursor, searchParams, setSearchParams])

  const handlePrevious = useCallback(() => {
    if (cursorHistory.length === 0) {
      return
    }

    const previousCursor = cursorHistory[cursorHistory.length - 1]
    setCursorHistory((history) => history.slice(0, -1))

    const params = new URLSearchParams(searchParams)
    if (previousCursor) {
      params.set('cursor', previousCursor)
    } else {
      params.delete('cursor')
    }
    setSearchParams(params)
  }, [cursorHistory, searchParams, setSearchParams])

  const summary = useMemo(() => {
    const count = data?.items.length ?? 0
    const page = cursorHistory.length + 1
    return `Page ${page} · Showing ${count} customer${count === 1 ? '' : 's'}`
  }, [cursorHistory.length, data?.items.length])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Customer search</h1>
        <p className="mt-1 text-sm text-slate-500">
          Search and filter customer profiles across the operations workspace.
        </p>
      </div>

      <CustomerSearchForm onSubmit={handleSearch} />

      <div className="space-y-0">
        <CustomerTable
          customers={data?.items ?? []}
          isLoading={isLoading}
          isError={isError}
        />

        {data && data.items.length > 0 ? (
          <Pagination
            summary={summary}
            hasPrevious={cursorHistory.length > 0}
            hasNext={Boolean(data.next_cursor)}
            onPrevious={handlePrevious}
            onNext={handleNext}
          />
        ) : null}
      </div>

      <p className="text-xs text-slate-400">Page size: {PAGE_SIZE} results per request.</p>
    </div>
  )
}
