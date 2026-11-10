import { apiRequest } from '@/lib/api'
import type { AssignableUser } from '@/types/user'

export async function fetchAssignableUsers(): Promise<AssignableUser[]> {
  return apiRequest<AssignableUser[]>('/users/assignable')
}
