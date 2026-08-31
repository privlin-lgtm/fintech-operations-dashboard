import { useState } from 'react'
import { useForm } from 'react-hook-form'

import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Select } from '@/components/ui/Select'
import { Can } from '@/features/auth/Can'
import { useDismissAlert, useEscalateAlert } from '@/features/alerts/hooks/useAlertSearch'
import type { ApiError } from '@/lib/api'
import { CASE_PRIORITY_OPTIONS, CASE_TYPE_OPTIONS } from '@/types/case'
import type { CasePriority, CaseType } from '@/types/case'
import type { Alert } from '@/types/alert'

type DismissValues = { reason: string }
type EscalateExistingValues = { caseId: string }
type EscalateNewValues = { caseType: CaseType; priority: CasePriority }

function errorMessage(error: unknown): string | null {
  if (!error) return null
  const apiError = error as ApiError
  return apiError.detail ?? apiError.message ?? 'Something went wrong.'
}

function DismissForm({ alertId }: { alertId: string }) {
  const mutation = useDismissAlert(alertId)
  const { register, handleSubmit, formState } = useForm<DismissValues>({
    defaultValues: { reason: '' },
  })

  const onSubmit = handleSubmit((values) => mutation.mutate(values))

  return (
    <form onSubmit={(event) => void onSubmit(event)} className="space-y-3">
      <div className="space-y-1.5">
        <label htmlFor="dismiss-reason" className="block text-sm font-medium text-slate-700">
          Reason
        </label>
        <input
          id="dismiss-reason"
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
          placeholder="Why doesn't this need investigation?"
          {...register('reason', { required: 'A reason is required to dismiss an alert.' })}
        />
        {formState.errors.reason ? (
          <p className="text-sm text-red-600">{formState.errors.reason.message}</p>
        ) : null}
      </div>
      {mutation.isError ? <p className="text-sm text-red-600">{errorMessage(mutation.error)}</p> : null}
      <Button type="submit" size="sm" variant="secondary" isLoading={mutation.isPending}>
        Dismiss
      </Button>
    </form>
  )
}

function EscalateForm({ alertId }: { alertId: string }) {
  const mutation = useEscalateAlert(alertId)
  const [mode, setMode] = useState<'existing' | 'new'>('new')

  const existingForm = useForm<EscalateExistingValues>({ defaultValues: { caseId: '' } })
  const newForm = useForm<EscalateNewValues>({ defaultValues: { caseType: 'fraud', priority: 'high' } })

  const onSubmitExisting = existingForm.handleSubmit((values) => {
    mutation.mutate({ case_id: values.caseId })
  })

  const onSubmitNew = newForm.handleSubmit((values) => {
    mutation.mutate({ create_case: true, case_type: values.caseType, priority: values.priority })
  })

  return (
    <div className="space-y-3">
      <div className="flex gap-4 text-sm text-slate-700">
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="escalate-mode"
            checked={mode === 'new'}
            onChange={() => setMode('new')}
          />
          Create a new case
        </label>
        <label className="flex items-center gap-2">
          <input
            type="radio"
            name="escalate-mode"
            checked={mode === 'existing'}
            onChange={() => setMode('existing')}
          />
          Link to an existing case
        </label>
      </div>

      {mode === 'new' ? (
        <form onSubmit={(event) => void onSubmitNew(event)} className="space-y-3">
          <Select label="Case type" options={CASE_TYPE_OPTIONS} {...newForm.register('caseType')} />
          <Select label="Priority" options={CASE_PRIORITY_OPTIONS} {...newForm.register('priority')} />
          {mutation.isError ? <p className="text-sm text-red-600">{errorMessage(mutation.error)}</p> : null}
          <Button type="submit" size="sm" isLoading={mutation.isPending}>
            Escalate
          </Button>
        </form>
      ) : (
        <form onSubmit={(event) => void onSubmitExisting(event)} className="space-y-3">
          <div className="space-y-1.5">
            <label htmlFor="escalate-case-id" className="block text-sm font-medium text-slate-700">
              Case ID
            </label>
            <input
              id="escalate-case-id"
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
              placeholder="Existing case UUID"
              {...existingForm.register('caseId', { required: 'A case ID is required.' })}
            />
            {existingForm.formState.errors.caseId ? (
              <p className="text-sm text-red-600">{existingForm.formState.errors.caseId.message}</p>
            ) : null}
          </div>
          {mutation.isError ? <p className="text-sm text-red-600">{errorMessage(mutation.error)}</p> : null}
          <Button type="submit" size="sm" isLoading={mutation.isPending}>
            Escalate
          </Button>
        </form>
      )}
    </div>
  )
}

export function AlertActionsPanel({ alert }: { alert: Alert }) {
  const isResolved = alert.status === 'dismissed' || alert.status === 'escalated'
  if (isResolved) {
    return null
  }

  return (
    <Can permission="alert:write">
      <div className="grid gap-6 xl:grid-cols-2">
        <Card title="Dismiss" description="No further action needed on this alert.">
          <DismissForm alertId={alert.id} />
        </Card>
        <Card title="Escalate" description="Send this alert into a case investigation.">
          <EscalateForm alertId={alert.id} />
        </Card>
      </div>
    </Can>
  )
}
