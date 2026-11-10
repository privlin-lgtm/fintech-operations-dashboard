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
import { formatCaseType, formatDateTime, formatLabel } from '@/lib/format'
import type { Case } from '@/types/case'

type CaseTableProps = {
  cases: Case[]
  isLoading: boolean
  isError: boolean
}

export function CaseTable({ cases, isLoading, isError }: CaseTableProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <Spinner label="Loading cases…" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        Unable to load cases.
      </div>
    )
  }

  if (cases.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <p className="text-base font-medium text-slate-900">No cases found</p>
        <p className="mt-1 text-sm text-slate-500">Try adjusting your filters.</p>
      </div>
    )
  }

  return (
    <Table>
      <TableHead>
        <TableHeaderCell>Case</TableHeaderCell>
        <TableHeaderCell>Type</TableHeaderCell>
        <TableHeaderCell>Status</TableHeaderCell>
        <TableHeaderCell>Priority</TableHeaderCell>
        <TableHeaderCell>SLA due</TableHeaderCell>
        <TableHeaderCell>Created</TableHeaderCell>
      </TableHead>
      <TableBody>
        {cases.map((caseItem) => (
          <TableRow key={caseItem.id}>
            <TableCell className="font-medium text-slate-900">
              <Link
                to={`/cases/${caseItem.id}`}
                className="text-brand-600 hover:text-brand-700 hover:underline"
              >
                {caseItem.case_number}
              </Link>
            </TableCell>
            <TableCell>{formatCaseType(caseItem.case_type)}</TableCell>
            <TableCell>{formatLabel(caseItem.status)}</TableCell>
            <TableCell>
              <Badge tone={riskTierTone(caseItem.priority)}>
                {formatLabel(caseItem.priority)}
              </Badge>
            </TableCell>
            <TableCell>{formatDateTime(caseItem.sla_due_at)}</TableCell>
            <TableCell>{formatDateTime(caseItem.created_at)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
