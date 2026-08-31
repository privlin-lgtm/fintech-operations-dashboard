import { skipToken, useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'

import { fetchCustomerProfile, searchCustomers } from '@/features/customers/customersApi'
import { parseEnumParam } from '@/lib/format'
import { customerKeys } from '@/lib/queryKeys'
import {
  CUSTOMER_SORT_OPTIONS,
  CUSTOMER_STATUS_OPTIONS,
  KYC_STATUS_OPTIONS,
  RISK_TIER_OPTIONS,
} from '@/types/customer'
import type { CustomerSearchParams } from '@/types/customer'

const PAGE_SIZE = 25
const STATUS_VALUES = CUSTOMER_STATUS_OPTIONS.map((option) => option.value)
const RISK_TIER_VALUES = RISK_TIER_OPTIONS.map((option) => option.value)
const KYC_STATUS_VALUES = KYC_STATUS_OPTIONS.map((option) => option.value)
const SORT_VALUES = CUSTOMER_SORT_OPTIONS.map((option) => option.value)

function parseSearchParams(searchParams: URLSearchParams): CustomerSearchParams {
  return {
    q: searchParams.get('q') ?? undefined,
    status: parseEnumParam(searchParams.get('status'), STATUS_VALUES),
    risk_tier: parseEnumParam(searchParams.get('risk_tier'), RISK_TIER_VALUES),
    kyc_status: parseEnumParam(searchParams.get('kyc_status'), KYC_STATUS_VALUES),
    sort: parseEnumParam(searchParams.get('sort'), SORT_VALUES) ?? '-created_at',
    cursor: searchParams.get('cursor') ?? undefined,
    limit: PAGE_SIZE,
  }
}

export function useCustomerSearch() {
  const [searchParams] = useSearchParams()
  const filters = parseSearchParams(searchParams)

  return useQuery({
    queryKey: customerKeys.list(filters),
    queryFn: () => searchCustomers(filters),
  })
}

export function useCustomerProfile(customerId: string | undefined) {
  return useQuery({
    queryKey: customerKeys.detail(customerId ?? ''),
    queryFn: customerId ? () => fetchCustomerProfile(customerId) : skipToken,
  })
}

export { PAGE_SIZE, parseSearchParams }
