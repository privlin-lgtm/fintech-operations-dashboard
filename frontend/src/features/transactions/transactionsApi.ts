import { apiRequest } from '@/lib/api'
import { buildQueryString, dateInputToIso, dateInputToIsoEnd, parseEnumParam } from '@/lib/format'
import type { PaginatedResponse } from '@/types/api'
import {
  TRANSACTION_CHANNEL_OPTIONS,
  TRANSACTION_DIRECTION_OPTIONS,
  TRANSACTION_SORT_OPTIONS,
  TRANSACTION_STATUS_OPTIONS,
} from '@/types/transaction'
import type { TransactionDetail, TransactionSearchParams, Transaction } from '@/types/transaction'

const STATUS_VALUES = TRANSACTION_STATUS_OPTIONS.map((option) => option.value)
const CHANNEL_VALUES = TRANSACTION_CHANNEL_OPTIONS.map((option) => option.value)
const DIRECTION_VALUES = TRANSACTION_DIRECTION_OPTIONS.map((option) => option.value)
const SORT_VALUES = TRANSACTION_SORT_OPTIONS.map((option) => option.value)

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

  return apiRequest<PaginatedResponse<Transaction>>(`/transactions${query}`)
}

export async function fetchTransactionDetail(transactionId: string): Promise<TransactionDetail> {
  return apiRequest<TransactionDetail>(`/transactions/${transactionId}`)
}

export function parseTransactionSearchParams(searchParams: URLSearchParams) {
  const minAmount = searchParams.get('min_amount')
  const maxAmount = searchParams.get('max_amount')
  const fromDate = searchParams.get('from_date')
  const toDate = searchParams.get('to_date')

  return {
    q: searchParams.get('q') ?? undefined,
    status: parseEnumParam(searchParams.get('status'), STATUS_VALUES),
    channel: parseEnumParam(searchParams.get('channel'), CHANNEL_VALUES),
    direction: parseEnumParam(searchParams.get('direction'), DIRECTION_VALUES),
    from_date: fromDate ? dateInputToIso(fromDate) : undefined,
    to_date: toDate ? dateInputToIsoEnd(toDate) : undefined,
    min_amount: minAmount ? Number(minAmount) : undefined,
    max_amount: maxAmount ? Number(maxAmount) : undefined,
    sort: parseEnumParam(searchParams.get('sort'), SORT_VALUES) ?? '-created_at',
    cursor: searchParams.get('cursor') ?? undefined,
    limit: 25,
  } satisfies TransactionSearchParams
}
