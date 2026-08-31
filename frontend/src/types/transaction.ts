export type TransactionStatus =
  | 'initiated'
  | 'pending'
  | 'settled'
  | 'failed'
  | 'reversed'

export type TransactionChannel = 'ach' | 'card' | 'wire' | 'internal'
export type TransactionDirection = 'debit' | 'credit'

export type TransactionSortField =
  | 'created_at'
  | '-created_at'
  | 'amount_cents'
  | '-amount_cents'
  | 'status'
  | '-status'
  | 'risk_score'
  | '-risk_score'

export type Transaction = {
  id: string
  account_id: string
  amount_cents: number
  currency: string
  direction: string
  channel: string
  status: string
  counterparty_masked: string | null
  risk_score: string | null
  settled_at: string | null
  has_open_alert: boolean
  has_open_case: boolean
  created_at: string
  updated_at: string
}

export type TransactionAccountSummary = {
  id: string
  customer_id: string
  masked_number: string
  account_type: string
}

export type TransactionStatusEvent = {
  status: string
  occurred_at: string
}

export type TransactionDetail = Transaction & {
  account: TransactionAccountSummary
  status_history: TransactionStatusEvent[]
  open_alert_count: number
  open_case_count: number
}

export type TransactionSearchParams = {
  q?: string
  customer_id?: string
  account_id?: string
  from_date?: string
  to_date?: string
  min_amount?: number
  max_amount?: number
  status?: TransactionStatus
  channel?: TransactionChannel
  direction?: TransactionDirection
  sort?: TransactionSortField
  limit?: number
  cursor?: string
}

export type TransactionSearchFormValues = {
  q: string
  status: '' | TransactionStatus
  channel: '' | TransactionChannel
  direction: '' | TransactionDirection
  from_date: string
  to_date: string
  min_amount: string
  max_amount: string
  sort: TransactionSortField
}

export const TRANSACTION_STATUS_OPTIONS = [
  { label: 'Initiated', value: 'initiated' as const },
  { label: 'Pending', value: 'pending' as const },
  { label: 'Settled', value: 'settled' as const },
  { label: 'Failed', value: 'failed' as const },
  { label: 'Reversed', value: 'reversed' as const },
]

export const TRANSACTION_CHANNEL_OPTIONS = [
  { label: 'ACH', value: 'ach' as const },
  { label: 'Card', value: 'card' as const },
  { label: 'Wire', value: 'wire' as const },
  { label: 'Internal', value: 'internal' as const },
]

export const TRANSACTION_DIRECTION_OPTIONS = [
  { label: 'Debit', value: 'debit' as const },
  { label: 'Credit', value: 'credit' as const },
]

export const TRANSACTION_SORT_OPTIONS = [
  { label: 'Newest first', value: '-created_at' as const },
  { label: 'Oldest first', value: 'created_at' as const },
  { label: 'Amount high–low', value: '-amount_cents' as const },
  { label: 'Amount low–high', value: 'amount_cents' as const },
  { label: 'Risk score', value: '-risk_score' as const },
]
