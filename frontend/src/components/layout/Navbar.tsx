import { Button } from '@/components/ui/Button'
import { useAuth } from '@/features/auth/AuthProvider'

export function Navbar() {
  const { user, logout } = useAuth()

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Welcome back</p>
        <h2 className="text-lg font-semibold text-slate-900">{user?.full_name ?? 'Operator'}</h2>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden text-right sm:block">
          <p className="text-sm font-medium text-slate-900">{user?.email}</p>
          <p className="text-xs capitalize text-slate-500">{user?.role?.name ?? 'analyst'}</p>
        </div>
        <Button variant="secondary" size="sm" onClick={() => void logout()}>
          Sign out
        </Button>
      </div>
    </header>
  )
}
