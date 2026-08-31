import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useSearchParams } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import type { AlertSearchFormValues } from '@/types/alert'
import {
  ALERT_SEVERITY_OPTIONS,
  ALERT_SORT_OPTIONS,
  ALERT_STATUS_OPTIONS,
  ALERT_TYPE_OPTIONS,
} from '@/types/alert'

type AlertSearchFormProps = {
  onSubmit: (values: AlertSearchFormValues) => void
}

function formValuesFromParams(searchParams: URLSearchParams): AlertSearchFormValues {
  return {
    q: searchParams.get('q') ?? '',
    status: (searchParams.get('status') as AlertSearchFormValues['status']) ?? '',
    severity: (searchParams.get('severity') as AlertSearchFormValues['severity']) ?? '',
    type: (searchParams.get('type') as AlertSearchFormValues['type']) ?? '',
    sort: (searchParams.get('sort') as AlertSearchFormValues['sort']) ?? '-created_at',
  }
}

export function AlertSearchForm({ onSubmit }: AlertSearchFormProps) {
  const [searchParams] = useSearchParams()
  const { register, handleSubmit, reset } = useForm<AlertSearchFormValues>({
    defaultValues: formValuesFromParams(searchParams),
  })

  useEffect(() => {
    reset(formValuesFromParams(searchParams))
  }, [reset, searchParams])

  return (
    <form
      className="grid gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-5"
      onSubmit={handleSubmit(onSubmit)}
    >
      <div className="lg:col-span-2">
        <Input label="Search" placeholder="Triggering reason" {...register('q')} />
      </div>
      <Select
        label="Status"
        options={[{ label: 'All statuses', value: '' }, ...ALERT_STATUS_OPTIONS]}
        {...register('status')}
      />
      <Select
        label="Severity"
        options={[{ label: 'All severities', value: '' }, ...ALERT_SEVERITY_OPTIONS]}
        {...register('severity')}
      />
      <Select
        label="Type"
        options={[{ label: 'All types', value: '' }, ...ALERT_TYPE_OPTIONS]}
        {...register('type')}
      />
      <Select label="Sort by" options={ALERT_SORT_OPTIONS} {...register('sort')} />
      <div className="flex items-end gap-2 lg:col-span-5">
        <Button type="submit">Apply filters</Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() =>
            onSubmit({ q: '', status: '', severity: '', type: '', sort: '-created_at' })
          }
        >
          Reset
        </Button>
      </div>
    </form>
  )
}
