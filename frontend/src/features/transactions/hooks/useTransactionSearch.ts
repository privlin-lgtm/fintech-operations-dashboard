import { skipToken, useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'

import {
  fetchTransactionDetail,
  parseTransactionSearchParams,
  searchTransactions,
} from '@/features/transactions/transactionsApi'
import { transactionKeys } from '@/lib/queryKeys'

export const TRANSACTION_PAGE_SIZE = 25

export function useTransactionSearch() {
  const [searchParams] = useSearchParams()
  const filters = parseTransactionSearchParams(searchParams)

  return useQuery({
    queryKey: transactionKeys.list(filters),
    queryFn: () => searchTransactions(filters),
  })
}

export function useTransactionDetail(transactionId: string | undefined) {
  return useQuery({
    queryKey: transactionKeys.detail(transactionId ?? ''),
    queryFn: transactionId ? () => fetchTransactionDetail(transactionId) : skipToken,
  })
}
