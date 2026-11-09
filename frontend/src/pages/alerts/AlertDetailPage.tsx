import { Link, useParams } from 'react-router-dom'

import { Badge, riskTierTone } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { Spinner } from '@/components/ui/Spinner'
import { AlertActionsPanel } from '@/features/alerts/components/AlertActionsPanel'
import { useAlertDetail } from '@/features/alerts/hooks/useAlertSearch'
import { formatDateTime, formatLabel, formatUserRef } from '@/lib/format'

export function AlertDetailPage() {
  const { alertId } = useParams<{ alertId: string }>()
  const { data: alert, isLoading, isError } = useAlertDetail(alertId)

  if (isLoading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <Spinner label="Loading alert…" />
      </div>
    )
  }

  if (isError || !alert) {
    return (
      <div className="space-y-4">
        <Link to="/alerts" className="text-sm font-medium text-brand-600 hover:text-brand-700">
          ← Back to alert search
        </Link>
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
          Alert not found.
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Link to="/alerts" className="text-sm font-medium text-brand-600 hover:text-brand-700">
            ← Back to alert search
          </Link>
          <h1 className="mt-2 text-2xl font-semibold text-slate-900">
            {formatLabel(alert.alert_type)}
          </h1>
          <p className="mt-1 text-sm text-slate-500">Alert workflow details</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge>{formatLabel(alert.status)}</Badge>
          <Badge tone={riskTierTone(alert.severity)}>{formatLabel(alert.severity)}</Badge>
        </div>
      </div>

      <Card title="Alert details">
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Triggering reason</dt>
            <dd className="max-w-xl text-right text-slate-900">{alert.triggering_reason}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Customer</dt>
            <dd>
              <Link
                to={`/customers/${alert.customer_id}`}
                className="text-brand-600 hover:underline"
              >
                View customer
              </Link>
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Transaction</dt>
            <dd>
              {alert.transaction_id ? (
                <Link
                  to={`/transactions/${alert.transaction_id}`}
                  className="text-brand-600 hover:underline"
                >
                  View transaction
                </Link>
              ) : (
                '—'
              )}
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Case</dt>
            <dd>
              {alert.case_id ? (
                <Link to={`/cases/${alert.case_id}`} className="text-brand-600 hover:underline">
                  View case
                </Link>
              ) : (
                '—'
              )}
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Assignee</dt>
            <dd data-testid="alert-assignee">{formatUserRef(alert.assignee_name, alert.assignee_id)}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Resolved</dt>
            <dd>{formatDateTime(alert.resolved_at)}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Resolution reason</dt>
            <dd>{alert.dismissal_reason ?? '—'}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Created</dt>
            <dd>{formatDateTime(alert.created_at)}</dd>
          </div>
        </dl>
      </Card>

      <AlertActionsPanel alert={alert} />
    </div>
  )
}
