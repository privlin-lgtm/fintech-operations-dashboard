import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'

import { fetchCustomerProfile, searchCustomers } from '@/features/customers/customersApi'
import type {
  CustomerSearchParams,
  CustomerStatus,
  KycStatus,
  RiskTier,
} from '@/types/customer'

const PAGE_SIZE = 25

function parseSearchParams(searchParams: URLSearchParams): CustomerSearchParams {
  const status = searchParams.get('status')
  const riskTier = searchParams.get('risk_tier')
  const kycStatus = searchParams.get('kyc_status')
  const sort = searchParams.get('sort')

  return {
    q: searchParams.get('q') ?? undefined,
    status: status ? (status as CustomerStatus) : undefined,
    risk_tier: riskTier ? (riskTier as RiskTier) : undefined,
    kyc_status: kycStatus ? (kycStatus as KycStatus) : undefined,
    sort: sort ? (sort as CustomerSearchParams['sort']) : '-created_at',
    cursor: searchParams.get('cursor') ?? undefined,
    limit: PAGE_SIZE,
  }
}

export function useCustomerSearch() {
  const [searchParams] = useSearchParams()
  const filters = parseSearchParams(searchParams)

  return useQuery({
    queryKey: ['customers', 'search', filters],
    queryFn: () => searchCustomers(filters),
  })
}

export function useCustomerProfile(customerId: string | undefined) {
  return useQuery({
    queryKey: ['customers', 'profile', customerId],
    queryFn: () => fetchCustomerProfile(customerId!),
    enabled: Boolean(customerId),
  })
}

export { PAGE_SIZE, parseSearchParams }
