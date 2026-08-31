import { apiRequest } from '@/lib/api'
import { getAccessToken } from '@/lib/storage'
import type { DashboardSummary } from '@/types/user'

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const token = getAccessToken()
  return apiRequest<DashboardSummary>('/reports/dashboard', { token })
}
