import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useSearchParams } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import type { ReportSearchFormValues } from '@/types/report'
import { groupOptionsForReport } from '@/types/report'
import type { ReportType } from '@/types/report'
import { toIsoDateInput } from '@/lib/format'

type ReportSearchFormProps = {
  reportType: ReportType
  defaultGroupBy: string
  onSubmit: (values: ReportSearchFormValues) => void
}

function formValuesFromParams(
  searchParams: URLSearchParams,
  defaultGroupBy: string,
): ReportSearchFormValues {
  return {
    from_date: toIsoDateInput(searchParams.get('from_date')),
    to_date: toIsoDateInput(searchParams.get('to_date')),
    group_by: searchParams.get('group_by') ?? defaultGroupBy,
  }
}

export function ReportSearchForm({ reportType, defaultGroupBy, onSubmit }: ReportSearchFormProps) {
  const [searchParams] = useSearchParams()
  const { register, handleSubmit, reset } = useForm<ReportSearchFormValues>({
    defaultValues: formValuesFromParams(searchParams, defaultGroupBy),
  })

  useEffect(() => {
    reset(formValuesFromParams(searchParams, defaultGroupBy))
  }, [defaultGroupBy, reset, searchParams])

  return (
    <form
      className="grid gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-4"
      onSubmit={handleSubmit(onSubmit)}
    >
      <Input label="From date" type="date" {...register('from_date')} />
      <Input label="To date" type="date" {...register('to_date')} />
      <Select
        label="Group by"
        options={groupOptionsForReport(reportType)}
        {...register('group_by')}
      />
      <div className="flex items-end gap-2">
        <Button type="submit">Run report</Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() =>
            onSubmit({ from_date: '', to_date: '', group_by: defaultGroupBy })
          }
        >
          Reset
        </Button>
      </div>
    </form>
  )
}
