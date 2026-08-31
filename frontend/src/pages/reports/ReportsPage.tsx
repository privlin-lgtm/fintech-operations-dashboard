import { Link } from 'react-router-dom'

import { Card } from '@/components/ui/Card'
import { REPORT_TYPE_OPTIONS } from '@/types/report'

export function ReportsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Reports</h1>
        <p className="mt-1 text-sm text-slate-500">
          Run operational reports with filters and export to CSV or PDF.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {REPORT_TYPE_OPTIONS.map((report) => (
          <Link key={report.value} to={`/reports/${report.value}`}>
            <Card
              title={report.label}
              description={report.description}
              className="transition hover:border-brand-200 hover:shadow-md"
            >
              <p className="text-sm font-medium text-brand-600">Open report →</p>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
