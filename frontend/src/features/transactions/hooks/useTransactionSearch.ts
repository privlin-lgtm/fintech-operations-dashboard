import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'

import {
  fetchTransactionDetail,
  parseTransactionSearchParams,
  searchTransactions,
} from '@/features/transactions/transactionsApi'

export const TRANSACTION_PAGE_SIZE = 25

export function useTransactionSearch() {
  const [searchParams] = useSearchParams()
  const filters = parseTransactionSearchParams(searchParams)

  return useQuery({
    queryKey: ['transactions', 'search', filters],
    queryFn: () => searchTransactions(filters),
  })
}

export function useTransactionDetail(transactionId: string | undefined) {
  return useQuery({
    queryKey: ['transactions', 'detail', transactionId],
    queryFn: () => fetchTransactionDetail(transactionId!),
    enabled: Boolean(transactionId),
  })
}
