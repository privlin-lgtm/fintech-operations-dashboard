import { useAuth } from '@/features/auth/AuthProvider'
import type { Permission } from '@/lib/permissions'
import { roleHasPermission } from '@/lib/permissions'

export function useHasPermission(permission: Permission): boolean {
  const { user } = useAuth()
  return roleHasPermission(user?.role?.name, permission)
}
