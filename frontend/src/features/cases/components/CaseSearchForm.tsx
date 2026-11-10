import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useSearchParams } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { AssigneeSelect } from '@/features/users/components/AssigneeSelect'
import { useAssignableUsers } from '@/features/users/useAssignableUsers'
import { useHasPermission } from '@/hooks/useHasPermission'
import { parseEnumParam } from '@/lib/format'
import type { CaseSearchFormValues } from '@/types/case'
import { CASE_PRIORITY_OPTIONS, CASE_STATUS_OPTIONS } from '@/types/case'

const STATUS_VALUES = CASE_STATUS_OPTIONS.map((option) => option.value)
const PRIORITY_VALUES = CASE_PRIORITY_OPTIONS.map((option) => option.value)

type CaseSearchFormProps = {
  onSubmit: (values: CaseSearchFormValues) => void
}

function formValuesFromParams(searchParams: URLSearchParams): CaseSearchFormValues {
  return {
    status: parseEnumParam(searchParams.get('status'), STATUS_VALUES) ?? '',
    priority: parseEnumParam(searchParams.get('priority'), PRIORITY_VALUES) ?? '',
    assignee: searchParams.get('assignee') ?? '',
    sla_risk: searchParams.get('sla_risk') === 'true',
  }
}

export function CaseSearchForm({ onSubmit }: CaseSearchFormProps) {
  const [searchParams] = useSearchParams()
  // Analysts only ever see their own cases (the backend pins the owner), so
  // the owner filter is only offered to roles that can list people.
  const canFilterByOwner = useHasPermission('user:assignable')
  const { data: people } = useAssignableUsers({ enabled: canFilterByOwner })
  const { register, handleSubmit, reset, getValues, setValue } = useForm<CaseSearchFormValues>({
    defaultValues: formValuesFromParams(searchParams),
  })

  useEffect(() => {
    reset(formValuesFromParams(searchParams))
  }, [reset, searchParams])

  // A select can't show an owner (e.g. from the URL) until that person's
  // option exists, so push the form's current value back into the DOM once
  // the list arrives. Uses the form's own value, never the URL, so a pick
  // the user already made is kept.
  useEffect(() => {
    if (people) setValue('assignee', getValues('assignee'))
  }, [people, getValues, setValue])

  return (
    <form
      className="grid gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-4"
      onSubmit={handleSubmit(onSubmit)}
    >
      <Select
        label="Status"
        options={[{ label: 'All statuses', value: '' }, ...CASE_STATUS_OPTIONS]}
        {...register('status')}
      />
      <Select
        label="Priority"
        options={[{ label: 'All priorities', value: '' }, ...CASE_PRIORITY_OPTIONS]}
        {...register('priority')}
      />
      {canFilterByOwner ? (
        <AssigneeSelect
          label="Owner"
          emptyLabel="Anyone"
          data-testid="case-search-owner"
          {...register('assignee')}
        />
      ) : null}
      <label className="flex items-end gap-2 pb-2 text-sm text-slate-700">
        <input type="checkbox" className="rounded border-slate-300" {...register('sla_risk')} />
        SLA at risk only
      </label>
      <div className="flex items-end gap-2 lg:col-span-4">
        <Button type="submit">Apply filters</Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() =>
            onSubmit({ status: '', priority: '', assignee: '', sla_risk: false })
          }
        >
          Reset
        </Button>
      </div>
    </form>
  )
}
