import { Link, useParams } from 'react-router-dom'

import { Badge, riskTierTone } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { Spinner } from '@/components/ui/Spinner'
import { CaseActionsPanel } from '@/features/cases/components/CaseActionsPanel'
import { useCaseDetail } from '@/features/cases/hooks/useCaseSearch'
import { formatCaseType, formatDateTime, formatLabel, formatResolutionCode, formatUserRef } from '@/lib/format'

export function CaseDetailPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const { data: caseItem, isLoading, isError } = useCaseDetail(caseId)

  if (isLoading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <Spinner label="Loading case…" />
      </div>
    )
  }

  if (isError || !caseItem) {
    return (
      <div className="space-y-4">
        <Link to="/cases" className="text-sm font-medium text-brand-600 hover:text-brand-700">
          ← Back to case search
        </Link>
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
          Case not found.
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Link to="/cases" className="text-sm font-medium text-brand-600 hover:text-brand-700">
            ← Back to case search
          </Link>
          <h1 className="mt-2 text-2xl font-semibold text-slate-900">{caseItem.case_number}</h1>
          <p className="mt-1 text-sm text-slate-500" data-testid="case-type">
            {formatCaseType(caseItem.case_type)} case
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge>{formatLabel(caseItem.status)}</Badge>
          <Badge tone={riskTierTone(caseItem.priority)}>
            {formatLabel(caseItem.priority)}
          </Badge>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card title="Case details">
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Customer</dt>
              <dd>
                <Link
                  to={`/customers/${caseItem.customer_id}`}
                  className="text-brand-600 hover:underline"
                >
                  View customer
                </Link>
              </dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Owner</dt>
              <dd data-testid="case-owner">{formatUserRef(caseItem.owner_name, caseItem.owner_id)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">SLA due</dt>
              <dd>{formatDateTime(caseItem.sla_due_at)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Closed</dt>
              <dd>{formatDateTime(caseItem.closed_at)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Resolution</dt>
              <dd data-testid="case-resolution">{formatResolutionCode(caseItem.resolution_code)}</dd>
            </div>
          </dl>
        </Card>

        <Card title="Notes" description="Investigation notes and system events.">
          {caseItem.notes.length === 0 ? (
            <p className="text-sm text-slate-500">No notes yet.</p>
          ) : (
            <ul className="space-y-3">
              {caseItem.notes.map((note) => (
                <li key={note.id} className="rounded-lg border border-slate-200 p-3 text-sm">
                  <p className="text-slate-700">{note.body}</p>
                  <p className="mt-2 text-xs text-slate-400">
                    {formatDateTime(note.created_at)}
                    {note.is_system ? ' · System' : ''}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {caseItem.closing_summary ? (
          <Card title="Closing summary" className="xl:col-span-2">
            <p className="text-sm text-slate-700">{caseItem.closing_summary}</p>
          </Card>
        ) : null}
      </div>

      <CaseActionsPanel caseItem={caseItem} />
    </div>
  )
}
