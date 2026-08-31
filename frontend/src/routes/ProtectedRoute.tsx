import { Navigate, Outlet } from 'react-router-dom'

import { Spinner } from '@/components/ui/Spinner'
import { useAuth } from '@/features/auth/AuthProvider'

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <Spinner label="Checking session…" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
