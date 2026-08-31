import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useSearchParams } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import type { CaseSearchFormValues } from '@/types/case'
import { CASE_PRIORITY_OPTIONS, CASE_STATUS_OPTIONS } from '@/types/case'

type CaseSearchFormProps = {
  onSubmit: (values: CaseSearchFormValues) => void
}

function formValuesFromParams(searchParams: URLSearchParams): CaseSearchFormValues {
  return {
    status: (searchParams.get('status') as CaseSearchFormValues['status']) ?? '',
    priority: (searchParams.get('priority') as CaseSearchFormValues['priority']) ?? '',
    assignee: searchParams.get('assignee') ?? '',
    sla_risk: searchParams.get('sla_risk') === 'true',
  }
}

export function CaseSearchForm({ onSubmit }: CaseSearchFormProps) {
  const [searchParams] = useSearchParams()
  const { register, handleSubmit, reset } = useForm<CaseSearchFormValues>({
    defaultValues: formValuesFromParams(searchParams),
  })

  useEffect(() => {
    reset(formValuesFromParams(searchParams))
  }, [reset, searchParams])

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
      <Input label="Assignee ID" placeholder="Owner UUID" {...register('assignee')} />
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
