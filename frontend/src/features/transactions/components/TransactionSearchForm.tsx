import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useSearchParams } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { toIsoDateInput } from '@/lib/format'
import type { TransactionSearchFormValues } from '@/types/transaction'
import {
  TRANSACTION_CHANNEL_OPTIONS,
  TRANSACTION_DIRECTION_OPTIONS,
  TRANSACTION_SORT_OPTIONS,
  TRANSACTION_STATUS_OPTIONS,
} from '@/types/transaction'

type TransactionSearchFormProps = {
  onSubmit: (values: TransactionSearchFormValues) => void
}

function formValuesFromParams(searchParams: URLSearchParams): TransactionSearchFormValues {
  return {
    q: searchParams.get('q') ?? '',
    status: (searchParams.get('status') as TransactionSearchFormValues['status']) ?? '',
    channel: (searchParams.get('channel') as TransactionSearchFormValues['channel']) ?? '',
    direction: (searchParams.get('direction') as TransactionSearchFormValues['direction']) ?? '',
    from_date: toIsoDateInput(searchParams.get('from_date')),
    to_date: toIsoDateInput(searchParams.get('to_date')),
    min_amount: searchParams.get('min_amount') ?? '',
    max_amount: searchParams.get('max_amount') ?? '',
    sort: (searchParams.get('sort') as TransactionSearchFormValues['sort']) ?? '-created_at',
  }
}

export function TransactionSearchForm({ onSubmit }: TransactionSearchFormProps) {
  const [searchParams] = useSearchParams()
  const { register, handleSubmit, reset } = useForm<TransactionSearchFormValues>({
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
      <div className="lg:col-span-2">
        <Input label="Search" placeholder="Counterparty or reference" {...register('q')} />
      </div>
      <Select
        label="Status"
        options={[{ label: 'All statuses', value: '' }, ...TRANSACTION_STATUS_OPTIONS]}
        {...register('status')}
      />
      <Select
        label="Channel"
        options={[{ label: 'All channels', value: '' }, ...TRANSACTION_CHANNEL_OPTIONS]}
        {...register('channel')}
      />
      <Select
        label="Direction"
        options={[{ label: 'All directions', value: '' }, ...TRANSACTION_DIRECTION_OPTIONS]}
        {...register('direction')}
      />
      <Input label="From date" type="date" {...register('from_date')} />
      <Input label="To date" type="date" {...register('to_date')} />
      <Input label="Min amount ($)" type="number" min="0" step="0.01" {...register('min_amount')} />
      <Input label="Max amount ($)" type="number" min="0" step="0.01" {...register('max_amount')} />
      <Select label="Sort by" options={TRANSACTION_SORT_OPTIONS} {...register('sort')} />
      <div className="flex items-end gap-2 lg:col-span-4">
        <Button type="submit">Apply filters</Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() =>
            onSubmit({
              q: '',
              status: '',
              channel: '',
              direction: '',
              from_date: '',
              to_date: '',
              min_amount: '',
              max_amount: '',
              sort: '-created_at',
            })
          }
        >
          Reset
        </Button>
      </div>
    </form>
  )
}
