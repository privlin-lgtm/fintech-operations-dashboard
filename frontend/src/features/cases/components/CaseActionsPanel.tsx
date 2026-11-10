import { useForm } from 'react-hook-form'

import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Select } from '@/components/ui/Select'
import { Can } from '@/features/auth/Can'
import {
  useAddCaseNote,
  useCloseCase,
  useReassignCase,
} from '@/features/cases/hooks/useCaseSearch'
import { AssigneeSelect } from '@/features/users/components/AssigneeSelect'
import { errorMessage } from '@/lib/errors'
import type { CaseDetail } from '@/types/case'

type AddNoteValues = { body: string }
type CloseCaseValues = { resolution_code: string; closing_summary: string; status: 'closed_resolved' | 'closed_no_action' }
type ReassignValues = { owner_id: string; reason: string }

function AddNoteForm({ caseId }: { caseId: string }) {
  const mutation = useAddCaseNote(caseId)
  const { register, handleSubmit, reset, formState } = useForm<AddNoteValues>({
    defaultValues: { body: '' },
  })

  const onSubmit = handleSubmit((values) => {
    mutation.mutate(
      { body: values.body },
      { onSuccess: () => reset({ body: '' }) },
    )
  })

  return (
    <form onSubmit={(event) => void onSubmit(event)} className="space-y-3">
      <div className="space-y-1.5">
        <label htmlFor="note-body" className="block text-sm font-medium text-slate-700">
          Add a note
        </label>
        <textarea
          id="note-body"
          rows={3}
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
          placeholder="What did you find, or what happened next?"
          {...register('body', { required: 'A note needs some text.' })}
        />
        {formState.errors.body ? (
          <p className="text-sm text-red-600">{formState.errors.body.message}</p>
        ) : null}
      </div>
      {mutation.isError ? <p className="text-sm text-red-600">{errorMessage(mutation.error)}</p> : null}
      <Button type="submit" size="sm" isLoading={mutation.isPending}>
        Add note
      </Button>
    </form>
  )
}

function CloseCaseForm({ caseId }: { caseId: string }) {
  const mutation = useCloseCase(caseId)
  const { register, handleSubmit, formState } = useForm<CloseCaseValues>({
    defaultValues: { resolution_code: '', closing_summary: '', status: 'closed_resolved' },
  })

  const onSubmit = handleSubmit((values) => {
    mutation.mutate(values)
  })

  return (
    <form onSubmit={(event) => void onSubmit(event)} className="space-y-3">
      <Select
        label="Outcome"
        options={[
          { label: 'Resolved', value: 'closed_resolved' },
          { label: 'No action needed', value: 'closed_no_action' },
        ]}
        {...register('status')}
      />
      <div className="space-y-1.5">
        <label htmlFor="resolution-code" className="block text-sm font-medium text-slate-700">
          Resolution code
        </label>
        <input
          id="resolution-code"
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
          placeholder="e.g. fraud_confirmed"
          {...register('resolution_code', { required: 'A resolution code is required to close a case.' })}
        />
        {formState.errors.resolution_code ? (
          <p className="text-sm text-red-600">{formState.errors.resolution_code.message}</p>
        ) : null}
      </div>
      <div className="space-y-1.5">
        <label htmlFor="closing-summary" className="block text-sm font-medium text-slate-700">
          Closing summary
        </label>
        <textarea
          id="closing-summary"
          rows={3}
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
          placeholder="Summarize the investigation and outcome for the record."
          {...register('closing_summary', { required: 'A closing summary is required to close a case.' })}
        />
        {formState.errors.closing_summary ? (
          <p className="text-sm text-red-600">{formState.errors.closing_summary.message}</p>
        ) : null}
      </div>
      {mutation.isError ? <p className="text-sm text-red-600">{errorMessage(mutation.error)}</p> : null}
      <Button type="submit" size="sm" variant="secondary" isLoading={mutation.isPending}>
        Close case
      </Button>
    </form>
  )
}

function ReassignForm({ caseId, currentOwnerId }: { caseId: string; currentOwnerId: string | null }) {
  const mutation = useReassignCase(caseId)
  const { register, handleSubmit, reset, formState } = useForm<ReassignValues>({
    defaultValues: { owner_id: '', reason: '' },
  })

  const onSubmit = handleSubmit((values) => {
    mutation.mutate(values, { onSuccess: () => reset({ owner_id: '', reason: '' }) })
  })

  return (
    <form
      data-testid="reassign-case-form"
      onSubmit={(event) => void onSubmit(event)}
      className="space-y-3"
    >
      <AssigneeSelect
        id="reassign-owner"
        data-testid="reassign-case-owner"
        label="New owner"
        excludeId={currentOwnerId}
        error={formState.errors.owner_id?.message}
        {...register('owner_id', { required: 'Choose who this case is going to.' })}
      />
      <div className="space-y-1.5">
        <label htmlFor="reassign-reason" className="block text-sm font-medium text-slate-700">
          Reason
        </label>
        <input
          id="reassign-reason"
          data-testid="reassign-case-reason"
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
          placeholder="Why is this handing off?"
          {...register('reason', { required: 'A reason is recorded with every reassignment.' })}
        />
        {formState.errors.reason ? (
          <p className="text-sm text-red-600">{formState.errors.reason.message}</p>
        ) : null}
      </div>
      {mutation.isError ? <p className="text-sm text-red-600">{errorMessage(mutation.error)}</p> : null}
      <Button
        type="submit"
        size="sm"
        variant="secondary"
        isLoading={mutation.isPending}
        data-testid="reassign-case-submit"
      >
        Reassign
      </Button>
    </form>
  )
}

export function CaseActionsPanel({ caseItem }: { caseItem: CaseDetail }) {
  const isClosed = caseItem.status.startsWith('closed')

  return (
    <div className="grid gap-6 xl:grid-cols-2">
      <Can permission="case:note">
        <Card title="Add note">
          <AddNoteForm caseId={caseItem.id} />
        </Card>
      </Can>
      {isClosed ? null : (
        <>
          <Can permission="case:close">
            <Card title="Close case" description="Requires a resolution code and a closing summary.">
              <CloseCaseForm caseId={caseItem.id} />
            </Card>
          </Can>
          <Can permission="case:reassign">
            <Card title="Reassign">
              <ReassignForm caseId={caseItem.id} currentOwnerId={caseItem.owner_id} />
            </Card>
          </Can>
        </>
      )}
    </div>
  )
}
