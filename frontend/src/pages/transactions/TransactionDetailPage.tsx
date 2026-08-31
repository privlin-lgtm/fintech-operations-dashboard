import { Link, useParams } from 'react-router-dom'

import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { Spinner } from '@/components/ui/Spinner'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '@/components/ui/Table'
import { useTransactionDetail } from '@/features/transactions/hooks/useTransactionSearch'
import { formatCurrency, formatDateTime, formatLabel } from '@/lib/format'

export function TransactionDetailPage() {
  const { transactionId } = useParams<{ transactionId: string }>()
  const { data: transaction, isLoading, isError } = useTransactionDetail(transactionId)

  if (isLoading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <Spinner label="Loading transaction…" />
      </div>
    )
  }

  if (isError || !transaction) {
    return (
      <div className="space-y-4">
        <Link to="/transactions" className="text-sm font-medium text-brand-600 hover:text-brand-700">
          ← Back to transaction search
        </Link>
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
          Transaction not found.
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <Link to="/transactions" className="text-sm font-medium text-brand-600 hover:text-brand-700">
          ← Back to transaction search
        </Link>
        <h1 className="mt-2 text-2xl font-semibold text-slate-900">
          {formatCurrency(transaction.amount_cents, transaction.currency)}
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          {formatLabel(transaction.direction)} · {formatLabel(transaction.channel)} ·{' '}
          {formatLabel(transaction.status)}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">Open alerts</p>
          <p className="mt-1 text-2xl font-semibold">{transaction.open_alert_count}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">Open cases</p>
          <p className="mt-1 text-2xl font-semibold">{transaction.open_case_count}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">Risk score</p>
          <p className="mt-1 text-2xl font-semibold">{transaction.risk_score ?? '—'}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs uppercase text-slate-500">Settled</p>
          <p className="mt-1 text-sm font-semibold">{formatDateTime(transaction.settled_at)}</p>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card title="Account">
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Account</dt>
              <dd>{transaction.account.masked_number}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Type</dt>
              <dd>{formatLabel(transaction.account.account_type)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Customer</dt>
              <dd>
                <Link
                  to={`/customers/${transaction.account.customer_id}`}
                  className="text-brand-600 hover:underline"
                >
                  View customer
                </Link>
              </dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Counterparty</dt>
              <dd>{transaction.counterparty_masked ?? '—'}</dd>
            </div>
          </dl>
        </Card>

        <Card title="Status history">
          {transaction.status_history.length === 0 ? (
            <p className="text-sm text-slate-500">No status history available.</p>
          ) : (
            <Table>
              <TableHead>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Occurred</TableHeaderCell>
              </TableHead>
              <TableBody>
                {transaction.status_history.map((event, index) => (
                  <TableRow key={`${event.status}-${index}`}>
                    <TableCell>
                      <Badge>{formatLabel(event.status)}</Badge>
                    </TableCell>
                    <TableCell>{formatDateTime(event.occurred_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>
      </div>
    </div>
  )
}
