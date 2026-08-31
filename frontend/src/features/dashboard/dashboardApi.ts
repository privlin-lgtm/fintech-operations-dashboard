import { apiRequest } from '@/lib/api'
import type { DashboardSummary } from '@/types/user'

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  return apiRequest<DashboardSummary>('/reports/dashboard')
}
