import { apiRequest } from '@/lib/api'
import { buildQueryString } from '@/lib/format'
import { getAccessToken } from '@/lib/storage'
import type { PaginatedResponse } from '@/types/api'
import type { Customer, CustomerProfile, CustomerSearchParams } from '@/types/customer'

function authHeaders() {
  return { token: getAccessToken() }
}

export async function searchCustomers(
  params: CustomerSearchParams,
): Promise<PaginatedResponse<Customer>> {
  const query = buildQueryString({
    q: params.q,
    status: params.status,
    risk_tier: params.risk_tier,
    kyc_status: params.kyc_status,
    sort: params.sort ?? '-created_at',
    limit: params.limit ?? 25,
    cursor: params.cursor,
  })

  return apiRequest<PaginatedResponse<Customer>>(`/customers${query}`, authHeaders())
}

export async function fetchCustomerProfile(customerId: string): Promise<CustomerProfile> {
  return apiRequest<CustomerProfile>(`/customers/${customerId}`, authHeaders())
}
