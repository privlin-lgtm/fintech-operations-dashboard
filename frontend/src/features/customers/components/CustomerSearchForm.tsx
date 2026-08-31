import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useSearchParams } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { parseEnumParam } from '@/lib/format'
import type { CustomerSearchFormValues } from '@/types/customer'
import {
  CUSTOMER_SORT_OPTIONS,
  CUSTOMER_STATUS_OPTIONS,
  KYC_STATUS_OPTIONS,
  RISK_TIER_OPTIONS,
} from '@/types/customer'

const STATUS_VALUES = CUSTOMER_STATUS_OPTIONS.map((option) => option.value)
const RISK_TIER_VALUES = RISK_TIER_OPTIONS.map((option) => option.value)
const KYC_STATUS_VALUES = KYC_STATUS_OPTIONS.map((option) => option.value)
const SORT_VALUES = CUSTOMER_SORT_OPTIONS.map((option) => option.value)

type CustomerSearchFormProps = {
  onSubmit: (values: CustomerSearchFormValues) => void
}

function formValuesFromParams(searchParams: URLSearchParams): CustomerSearchFormValues {
  return {
    q: searchParams.get('q') ?? '',
    status: parseEnumParam(searchParams.get('status'), STATUS_VALUES) ?? '',
    risk_tier: parseEnumParam(searchParams.get('risk_tier'), RISK_TIER_VALUES) ?? '',
    kyc_status: parseEnumParam(searchParams.get('kyc_status'), KYC_STATUS_VALUES) ?? '',
    sort: parseEnumParam(searchParams.get('sort'), SORT_VALUES) ?? '-created_at',
  }
}

export function CustomerSearchForm({ onSubmit }: CustomerSearchFormProps) {
  const [searchParams] = useSearchParams()
  const { register, handleSubmit, reset } = useForm<CustomerSearchFormValues>({
    defaultValues: formValuesFromParams(searchParams),
  })

  useEffect(() => {
    reset(formValuesFromParams(searchParams))
  }, [reset, searchParams])

  return (
    <form
      className="grid gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-6"
      data-testid="customer-search-form"
      onSubmit={handleSubmit(onSubmit)}
    >
      <div className="lg:col-span-2">
        <Input
          label="Search"
          placeholder="Name, email, or phone"
          data-testid="customer-search-query"
          {...register('q')}
        />
      </div>

      <Select
        label="Status"
        options={[{ label: 'All statuses', value: '' }, ...CUSTOMER_STATUS_OPTIONS]}
        {...register('status')}
      />

      <Select
        label="Risk tier"
        options={[{ label: 'All risk tiers', value: '' }, ...RISK_TIER_OPTIONS]}
        {...register('risk_tier')}
      />

      <Select
        label="KYC status"
        options={[{ label: 'All KYC statuses', value: '' }, ...KYC_STATUS_OPTIONS]}
        {...register('kyc_status')}
      />

      <Select label="Sort by" options={CUSTOMER_SORT_OPTIONS} {...register('sort')} />

      <div className="flex items-end gap-2 lg:col-span-6">
        <Button type="submit">Apply filters</Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() =>
            onSubmit({
              q: '',
              status: '',
              risk_tier: '',
              kyc_status: '',
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
