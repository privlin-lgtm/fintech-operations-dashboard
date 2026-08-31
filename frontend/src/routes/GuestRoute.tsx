import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'

import { useAuth } from '@/features/auth/AuthProvider'

export function GuestRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return null
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return children
}
