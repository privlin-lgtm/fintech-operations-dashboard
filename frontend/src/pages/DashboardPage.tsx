import { useQuery } from '@tanstack/react-query'

import { Card } from '@/components/ui/Card'
import { Spinner } from '@/components/ui/Spinner'
import { fetchDashboardSummary } from '@/features/dashboard/dashboardApi'
import { dashboardKeys } from '@/lib/queryKeys'

type StatCardProps = {
  label: string
  value: number
  tone?: 'default' | 'warning' | 'success'
}

function StatCard({ label, value, tone = 'default' }: StatCardProps) {
  const toneClasses = {
    default: 'text-slate-900',
    warning: 'text-amber-600',
    success: 'text-emerald-600',
  }

  return (
    <Card className="p-4">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className={`mt-2 text-3xl font-semibold ${toneClasses[tone]}`}>{value}</p>
    </Card>
  )
}

export function DashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: dashboardKeys.summary(),
    queryFn: fetchDashboardSummary,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Operations dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">
          Live snapshot of cases, alerts, and SLA risk across your queue.
        </p>
      </div>

      {isLoading ? <Spinner label="Loading dashboard metrics…" /> : null}

      {isError ? (
        <Card>
          <p className="text-sm text-red-600">
            Unable to load dashboard metrics. Confirm the API is running on port 8000.
          </p>
        </Card>
      ) : null}

      {data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Open cases" value={data.open_cases} />
            <StatCard label="SLA at risk" value={data.sla_at_risk} tone="warning" />
            <StatCard label="New alerts" value={data.new_alerts} />
            <StatCard
              label="Cases closed today"
              value={data.cases_closed_today}
              tone="success"
            />
          </div>

        </>
      ) : null}
    </div>
  )
}
