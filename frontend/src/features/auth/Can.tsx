import type { ReactNode } from 'react'

import { useHasPermission } from '@/hooks/useHasPermission'
import type { Permission } from '@/lib/permissions'

type CanProps = {
  permission: Permission
  children: ReactNode
  fallback?: ReactNode
}

/**
 * UX-only gate — hides an action the backend would reject anyway. Never the
 * only thing standing between a role and an action: the backend's own
 * require_roles(...) is what actually enforces this.
 */
export function Can({ permission, children, fallback = null }: CanProps) {
  const allowed = useHasPermission(permission)
  return allowed ? children : fallback
}
