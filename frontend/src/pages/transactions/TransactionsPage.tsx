import { useCallback } from 'react'

import { Pagination } from '@/components/ui/Pagination'
import { TransactionSearchForm } from '@/features/transactions/components/TransactionSearchForm'
import { TransactionTable } from '@/features/transactions/components/TransactionTable'
import {
  TRANSACTION_PAGE_SIZE,
  useTransactionSearch,
} from '@/features/transactions/hooks/useTransactionSearch'
import { setSearchParam, useCursorPagination } from '@/hooks/useCursorPagination'
import type { TransactionSearchFormValues } from '@/types/transaction'

export function TransactionsPage() {
  const { data, isLoading, isError } = useTransactionSearch()
  const { applySearchParams, goNext, goPrevious, hasPrevious, summary } =
    useCursorPagination('transaction')

  const handleSearch = useCallback(
    (values: TransactionSearchFormValues) => {
      const params = new URLSearchParams()
      setSearchParam(params, 'q', values.q.trim())
      setSearchParam(params, 'status', values.status)
      setSearchParam(params, 'channel', values.channel)
      setSearchParam(params, 'direction', values.direction)
      setSearchParam(params, 'from_date', values.from_date)
      setSearchParam(params, 'to_date', values.to_date)
      setSearchParam(
        params,
        'min_amount',
        values.min_amount ? String(Math.round(Number(values.min_amount) * 100)) : undefined,
      )
      setSearchParam(
        params,
        'max_amount',
        values.max_amount ? String(Math.round(Number(values.max_amount) * 100)) : undefined,
      )
      setSearchParam(params, 'sort', values.sort)
      applySearchParams(params)
    },
    [applySearchParams],
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Transaction search</h1>
        <p className="mt-1 text-sm text-slate-500">
          Search and filter transaction activity across accounts.
        </p>
      </div>

      <TransactionSearchForm onSubmit={handleSearch} />

      <div className="space-y-0">
        <TransactionTable
          transactions={data?.items ?? []}
          isLoading={isLoading}
          isError={isError}
        />
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

      <p className="text-xs text-slate-400">Page size: {TRANSACTION_PAGE_SIZE} results per request.</p>
    </div>
  )
}
