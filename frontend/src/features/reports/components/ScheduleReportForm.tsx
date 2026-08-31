import { useForm } from 'react-hook-form'

import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Select } from '@/components/ui/Select'
import { Can } from '@/features/auth/Can'
import { useCreateReportSchedule } from '@/features/reports/hooks/useReport'
import type { ApiError } from '@/lib/api'
import { REPORT_CADENCE_OPTIONS } from '@/types/report'
import type { ReportCadence, ReportType } from '@/types/report'

type ScheduleFormValues = {
  cadence: ReportCadence
  recipients: string
}

function errorMessage(error: unknown): string | null {
  if (!error) return null
  const apiError = error as ApiError
  return apiError.detail ?? apiError.message ?? 'Something went wrong.'
}

function ScheduleReportFormInner({ reportType }: { reportType: ReportType }) {
  const mutation = useCreateReportSchedule()
  const { register, handleSubmit, reset, formState } = useForm<ScheduleFormValues>({
    defaultValues: { cadence: 'weekly', recipients: '' },
  })

  const onSubmit = handleSubmit((values) => {
    const recipients = values.recipients
      .split(',')
      .map((email) => email.trim())
      .filter(Boolean)

    mutation.mutate(
      { report_type: reportType, cadence: values.cadence, recipients },
      { onSuccess: () => reset({ cadence: values.cadence, recipients: '' }) },
    )
  })

  return (
    <Card title="Schedule this report" description="Send this report to a distribution list on a recurring cadence.">
      <form onSubmit={(event) => void onSubmit(event)} className="grid gap-4 sm:grid-cols-3">
        <Select label="Cadence" options={REPORT_CADENCE_OPTIONS} {...register('cadence')} />
        <div className="space-y-1.5 sm:col-span-2">
          <label htmlFor="schedule-recipients" className="block text-sm font-medium text-slate-700">
            Recipients
          </label>
          <input
            id="schedule-recipients"
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
            placeholder="lead@example.com, compliance@example.com"
            {...register('recipients', { required: 'At least one recipient is required.' })}
          />
          {formState.errors.recipients ? (
            <p className="text-sm text-red-600">{formState.errors.recipients.message}</p>
          ) : null}
        </div>
        <div className="sm:col-span-3">
          {mutation.isSuccess ? (
            <p className="mb-2 text-sm text-emerald-600">Schedule created.</p>
          ) : null}
          {mutation.isError ? (
            <p className="mb-2 text-sm text-red-600">{errorMessage(mutation.error)}</p>
          ) : null}
          <Button type="submit" size="sm" isLoading={mutation.isPending}>
            Create schedule
          </Button>
        </div>
      </form>
    </Card>
  )
}

export function ScheduleReportForm({ reportType }: { reportType: ReportType }) {
  return (
    <Can permission="report:schedule">
      <ScheduleReportFormInner reportType={reportType} />
    </Can>
  )
}
