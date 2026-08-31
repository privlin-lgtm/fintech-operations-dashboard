import { Link } from 'react-router-dom'

import {
  Badge,
  customerStatusTone,
  kycStatusTone,
  riskTierTone,
} from '@/components/ui/Badge'
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
import type { Customer } from '@/types/customer'

type CustomerTableProps = {
  customers: Customer[]
  isLoading: boolean
  isError: boolean
}

export function CustomerTable({ customers, isLoading, isError }: CustomerTableProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <Spinner label="Loading customers…" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
        Unable to load customers. Confirm you are signed in and the API is running.
      </div>
    )
  }

  if (customers.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <p className="text-base font-medium text-slate-900">No customers found</p>
        <p className="mt-1 text-sm text-slate-500">Try adjusting your search or filters.</p>
      </div>
    )
  }

  return (
    <Table>
      <TableHead>
        <TableHeaderCell>Name</TableHeaderCell>
        <TableHeaderCell>Email</TableHeaderCell>
        <TableHeaderCell>Phone</TableHeaderCell>
        <TableHeaderCell>Status</TableHeaderCell>
        <TableHeaderCell>Risk</TableHeaderCell>
        <TableHeaderCell>KYC</TableHeaderCell>
        <TableHeaderCell>Created</TableHeaderCell>
      </TableHead>
      <TableBody>
        {customers.map((customer) => (
          <TableRow key={customer.id}>
            <TableCell className="font-medium text-slate-900">
              <Link
                to={`/customers/${customer.id}`}
                className="text-brand-600 hover:text-brand-700 hover:underline"
              >
                {customer.full_name}
              </Link>
            </TableCell>
            <TableCell>{customer.email ?? '—'}</TableCell>
            <TableCell>{customer.phone ?? '—'}</TableCell>
            <TableCell>
              <Badge tone={customerStatusTone(customer.status)}>
                {formatLabel(customer.status)}
              </Badge>
            </TableCell>
            <TableCell>
              <Badge tone={riskTierTone(customer.risk_tier)}>
                {formatLabel(customer.risk_tier)}
              </Badge>
            </TableCell>
            <TableCell>
              <Badge tone={kycStatusTone(customer.kyc_status)}>
                {formatLabel(customer.kyc_status)}
              </Badge>
            </TableCell>
            <TableCell>{formatDateTime(customer.created_at)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
