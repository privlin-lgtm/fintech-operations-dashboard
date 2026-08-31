import { Link } from 'react-router-dom'

import { Badge, riskTierTone } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '@/components/ui/Table'
import { formatDateTime, formatLabel } from '@/lib/format'
import type { Alert } from '@/types/alert'

type AlertTableProps = {
  alerts: Alert[]
  isLoading: boolean
  isError: boolean
}

export function AlertTable({ alerts, isLoading, isError }: AlertTableProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <Spinner label="Loading alerts…" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        Unable to load alerts.
      </div>
    )
  }

  if (alerts.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <p className="text-base font-medium text-slate-900">No alerts found</p>
        <p className="mt-1 text-sm text-slate-500">Try adjusting your search or filters.</p>
      </div>
    )
  }

  return (
    <Table>
      <TableHead>
        <TableHeaderCell>Type</TableHeaderCell>
        <TableHeaderCell>Severity</TableHeaderCell>
        <TableHeaderCell>Status</TableHeaderCell>
        <TableHeaderCell>Reason</TableHeaderCell>
        <TableHeaderCell>Created</TableHeaderCell>
      </TableHead>
      <TableBody>
        {alerts.map((alert) => (
          <TableRow key={alert.id}>
            <TableCell className="font-medium text-slate-900">
              <Link
                to={`/alerts/${alert.id}`}
                className="text-brand-600 hover:text-brand-700 hover:underline"
              >
                {formatLabel(alert.alert_type)}
              </Link>
            </TableCell>
            <TableCell>
              <Badge tone={riskTierTone(alert.severity)}>{formatLabel(alert.severity)}</Badge>
            </TableCell>
            <TableCell>{formatLabel(alert.status)}</TableCell>
            <TableCell className="max-w-xs truncate">{alert.triggering_reason}</TableCell>
            <TableCell>{formatDateTime(alert.created_at)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
