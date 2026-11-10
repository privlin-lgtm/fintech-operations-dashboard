import { Link, useParams } from 'react-router-dom'

import {
  Badge,
  customerStatusTone,
  kycStatusTone,
  riskTierTone,
} from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { Spinner } from '@/components/ui/Spinner'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeaderCell,
  TableRow,
} from '@/components/ui/Table'
import { useCustomerProfile } from '@/features/customers/hooks/useCustomerSearch'
import { OpenCasePanel } from '@/features/cases/components/OpenCasePanel'
import { formatCaseType, formatDateTime, formatLabel } from '@/lib/format'

function StatBlock({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  )
}

export function CustomerDetailPage() {
  const { customerId } = useParams<{ customerId: string }>()
  const { data: customer, isLoading, isError } = useCustomerProfile(customerId)

  if (isLoading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <Spinner label="Loading customer profile…" />
      </div>
    )
  }

  if (isError || !customer) {
    return (
      <div className="space-y-4">
        <Link to="/customers" className="text-sm font-medium text-brand-600 hover:text-brand-700">
          ← Back to customer search
        </Link>
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
          Customer not found or you do not have permission to view this profile.
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Link
            to="/customers"
            className="text-sm font-medium text-brand-600 hover:text-brand-700"
          >
            ← Back to customer search
          </Link>
          <h1 className="mt-2 text-2xl font-semibold text-slate-900">{customer.full_name}</h1>
          <p className="mt-1 text-sm text-slate-500">Customer profile and recent activity</p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Badge tone={customerStatusTone(customer.status)}>
            {formatLabel(customer.status)}
          </Badge>
          <Badge tone={riskTierTone(customer.risk_tier)}>
            Risk: {formatLabel(customer.risk_tier)}
          </Badge>
          <Badge tone={kycStatusTone(customer.kyc_status)}>
            KYC: {formatLabel(customer.kyc_status)}
          </Badge>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatBlock label="Accounts" value={customer.account_count} />
        <StatBlock label="Open cases" value={customer.open_case_count} />
        <StatBlock label="Total cases" value={customer.total_case_count} />
        <StatBlock label="Open alerts" value={customer.open_alert_count} />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <OpenCasePanel customerId={customer.id} />

        <Card title="Contact details">
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Email</dt>
              <dd className="font-medium text-slate-900">{customer.email ?? '—'}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Phone</dt>
              <dd className="font-medium text-slate-900">{customer.phone ?? '—'}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Created</dt>
              <dd className="font-medium text-slate-900">{formatDateTime(customer.created_at)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Updated</dt>
              <dd className="font-medium text-slate-900">{formatDateTime(customer.updated_at)}</dd>
            </div>
          </dl>
        </Card>

        <Card title="Recent accounts" description="Latest linked accounts for this customer.">
          {customer.recent_accounts.length === 0 ? (
            <p className="text-sm text-slate-500">No accounts on file.</p>
          ) : (
            <Table>
              <TableHead>
                <TableHeaderCell>Type</TableHeaderCell>
                <TableHeaderCell>Number</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
              </TableHead>
              <TableBody>
                {customer.recent_accounts.map((account) => (
                  <TableRow key={account.id}>
                    <TableCell>{formatLabel(account.account_type)}</TableCell>
                    <TableCell>{account.masked_number}</TableCell>
                    <TableCell>{formatLabel(account.status)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>

        <Card title="Recent cases" description="Most recent investigations involving this customer.">
          {customer.recent_cases.length === 0 ? (
            <p className="text-sm text-slate-500">No cases on file.</p>
          ) : (
            <Table>
              <TableHead>
                <TableHeaderCell>Case</TableHeaderCell>
                <TableHeaderCell>Type</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
              </TableHead>
              <TableBody>
                {customer.recent_cases.map((caseItem) => (
                  <TableRow key={caseItem.id}>
                    <TableCell className="font-medium text-slate-900">
                      {caseItem.case_number}
                    </TableCell>
                    <TableCell>{formatCaseType(caseItem.case_type)}</TableCell>
                    <TableCell>{formatLabel(caseItem.status)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>

        <Card title="Recent alerts" description="Latest alerts raised for this customer.">
          {customer.recent_alerts.length === 0 ? (
            <p className="text-sm text-slate-500">No alerts on file.</p>
          ) : (
            <Table>
              <TableHead>
                <TableHeaderCell>Type</TableHeaderCell>
                <TableHeaderCell>Severity</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
              </TableHead>
              <TableBody>
                {customer.recent_alerts.map((alert) => (
                  <TableRow key={alert.id}>
                    <TableCell>{formatLabel(alert.alert_type)}</TableCell>
                    <TableCell>
                      <Badge tone={riskTierTone(alert.severity)}>
                        {formatLabel(alert.severity)}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatLabel(alert.status)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>
      </div>
    </div>
  )
}
