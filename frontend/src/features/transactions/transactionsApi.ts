import { apiRequest } from '@/lib/api'
import { buildQueryString, dateInputToIso, dateInputToIsoEnd } from '@/lib/format'
import { getAccessToken } from '@/lib/storage'
import type { PaginatedResponse } from '@/types/api'
import type {
  TransactionChannel,
  TransactionDetail,
  TransactionDirection,
  TransactionSearchParams,
  TransactionStatus,
  Transaction,
} from '@/types/transaction'

function authHeaders() {
  return { token: getAccessToken() }
}

export async function searchTransactions(
  params: TransactionSearchParams,
): Promise<PaginatedResponse<Transaction>> {
  const query = buildQueryString({
    q: params.q,
    customer_id: params.customer_id,
    account_id: params.account_id,
    from: params.from_date,
    to: params.to_date,
    min_amount: params.min_amount,
    max_amount: params.max_amount,
    status: params.status,
    channel: params.channel,
    direction: params.direction,
    sort: params.sort ?? '-created_at',
    limit: params.limit ?? 25,
    cursor: params.cursor,
  })

  return apiRequest<PaginatedResponse<Transaction>>(`/transactions${query}`, authHeaders())
}

export async function fetchTransactionDetail(transactionId: string): Promise<TransactionDetail> {
  return apiRequest<TransactionDetail>(`/transactions/${transactionId}`, authHeaders())
}

export function parseTransactionSearchParams(searchParams: URLSearchParams) {
  const minAmount = searchParams.get('min_amount')
  const maxAmount = searchParams.get('max_amount')
  const fromDate = searchParams.get('from_date')
  const toDate = searchParams.get('to_date')

  return {
    q: searchParams.get('q') ?? undefined,
    status: (searchParams.get('status') as TransactionStatus) || undefined,
    channel: (searchParams.get('channel') as TransactionChannel) || undefined,
    direction: (searchParams.get('direction') as TransactionDirection) || undefined,
    from_date: fromDate ? dateInputToIso(fromDate) : undefined,
    to_date: toDate ? dateInputToIsoEnd(toDate) : undefined,
    min_amount: minAmount ? Number(minAmount) : undefined,
    max_amount: maxAmount ? Number(maxAmount) : undefined,
    sort: (searchParams.get('sort') as TransactionSearchParams['sort']) ?? '-created_at',
    cursor: searchParams.get('cursor') ?? undefined,
    limit: 25,
  } satisfies TransactionSearchParams
}
