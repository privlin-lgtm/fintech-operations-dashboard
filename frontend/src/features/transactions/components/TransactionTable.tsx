import { Link } from 'react-router-dom'

import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '@/components/ui/Table'
import { formatCurrency, formatDateTime, formatLabel } from '@/lib/format'
import type { Transaction } from '@/types/transaction'

type TransactionTableProps = {
  transactions: Transaction[]
  isLoading: boolean
  isError: boolean
}

export function TransactionTable({ transactions, isLoading, isError }: TransactionTableProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <Spinner label="Loading transactions…" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        Unable to load transactions.
      </div>
    )
  }

  if (transactions.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <p className="text-base font-medium text-slate-900">No transactions found</p>
        <p className="mt-1 text-sm text-slate-500">Try adjusting your search or filters.</p>
      </div>
    )
  }

  return (
    <Table>
      <TableHead>
        <TableHeaderCell>Amount</TableHeaderCell>
        <TableHeaderCell>Direction</TableHeaderCell>
        <TableHeaderCell>Channel</TableHeaderCell>
        <TableHeaderCell>Status</TableHeaderCell>
        <TableHeaderCell>Risk</TableHeaderCell>
        <TableHeaderCell>Flags</TableHeaderCell>
        <TableHeaderCell>Created</TableHeaderCell>
      </TableHead>
      <TableBody>
        {transactions.map((transaction) => (
          <TableRow key={transaction.id}>
            <TableCell className="font-medium text-slate-900">
              <Link
                to={`/transactions/${transaction.id}`}
                className="text-brand-600 hover:text-brand-700 hover:underline"
              >
                {formatCurrency(transaction.amount_cents, transaction.currency)}
              </Link>
            </TableCell>
            <TableCell>{formatLabel(transaction.direction)}</TableCell>
            <TableCell>{formatLabel(transaction.channel)}</TableCell>
            <TableCell>{formatLabel(transaction.status)}</TableCell>
            <TableCell>{transaction.risk_score ?? '—'}</TableCell>
            <TableCell>
              <div className="flex gap-1">
                {transaction.has_open_alert ? <Badge tone="warning">Alert</Badge> : null}
                {transaction.has_open_case ? <Badge tone="info">Case</Badge> : null}
                {!transaction.has_open_alert && !transaction.has_open_case ? '—' : null}
              </div>
            </TableCell>
            <TableCell>{formatDateTime(transaction.created_at)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
