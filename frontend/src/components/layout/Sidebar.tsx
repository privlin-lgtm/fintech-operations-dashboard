import { NavLink } from 'react-router-dom'

type NavItem = {
  label: string
  to: string
  icon: string
}

const navItems: NavItem[] = [
  { label: 'Dashboard', to: '/', icon: '◫' },
  { label: 'Customers', to: '/customers', icon: '◎' },
  { label: 'Transactions', to: '/transactions', icon: '⇄' },
  { label: 'Cases', to: '/cases', icon: '▣' },
  { label: 'Alerts', to: '/alerts', icon: '⚑' },
  { label: 'Reports', to: '/reports', icon: '▤' },
]

export function Sidebar() {
  return (
    <aside data-testid="app-sidebar" className="flex w-64 shrink-0 flex-col bg-sidebar text-white">
      <div className="border-b border-white/10 px-5 py-6">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sidebar-muted">
          Fintech Ops
        </p>
        <h1 className="mt-1 text-lg font-semibold">Operations Dashboard</h1>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                isActive
                  ? 'bg-white/10 text-white'
                  : 'text-sidebar-muted hover:bg-white/5 hover:text-white'
              }`
            }
          >
            <span aria-hidden className="text-base">
              {item.icon}
            </span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-white/10 px-5 py-4 text-xs text-sidebar-muted">
        Secure operations workspace
      </div>
    </aside>
  )
}
