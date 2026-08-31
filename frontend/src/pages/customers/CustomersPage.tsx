import { useCallback } from 'react'

import { Pagination } from '@/components/ui/Pagination'
import { CustomerSearchForm } from '@/features/customers/components/CustomerSearchForm'
import { CustomerTable } from '@/features/customers/components/CustomerTable'
import { PAGE_SIZE, useCustomerSearch } from '@/features/customers/hooks/useCustomerSearch'
import { setSearchParam, useCursorPagination } from '@/hooks/useCursorPagination'
import type { CustomerSearchFormValues } from '@/types/customer'

export function CustomersPage() {
  const { data, isLoading, isError } = useCustomerSearch()
  const { applySearchParams, goNext, goPrevious, hasPrevious, summary } =
    useCursorPagination('customer')

  const handleSearch = useCallback(
    (values: CustomerSearchFormValues) => {
      const params = new URLSearchParams()
      setSearchParam(params, 'q', values.q.trim())
      setSearchParam(params, 'status', values.status)
      setSearchParam(params, 'risk_tier', values.risk_tier)
      setSearchParam(params, 'kyc_status', values.kyc_status)
      setSearchParam(params, 'sort', values.sort)
      applySearchParams(params)
    },
    [applySearchParams],
  )

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
            summary={summary(data.items.length)}
            hasPrevious={hasPrevious}
            hasNext={Boolean(data.next_cursor)}
            onPrevious={goPrevious}
            onNext={() => goNext(data.next_cursor)}
          />
        ) : null}
      </div>

      <p className="text-xs text-slate-400">Page size: {PAGE_SIZE} results per request.</p>
    </div>
  )
}
