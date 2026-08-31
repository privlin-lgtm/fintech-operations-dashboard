import { useCallback, useState } from 'react'
import { Link, Navigate, useParams, useSearchParams } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
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
import { ReportSearchForm } from '@/features/reports/components/ReportSearchForm'
import { ScheduleReportForm } from '@/features/reports/components/ScheduleReportForm'
import { downloadReport } from '@/features/reports/reportsApi'
import { useReport } from '@/features/reports/hooks/useReport'
import { setSearchParam } from '@/hooks/useCursorPagination'
import {
  formatCurrency,
  formatLabel,
  formatPercent,
} from '@/lib/format'
import type {
  AlertVolumeReport,
  CaseVolumeReport,
  ReportSearchFormValues,
  ReportType,
  SlaPerformanceReport,
  TransactionVolumeReport,
} from '@/types/report'
import { REPORT_TYPE_OPTIONS, defaultGroupByForReport } from '@/types/report'

function isReportType(value: string | undefined): value is ReportType {
  return value === 'transactions' || value === 'cases' || value === 'alerts' || value === 'sla'
}

function VolumeResultsTable({
  rows,
  amountColumn,
}: {
  rows: { group: string; count: number; total_amount_cents?: number }[]
  amountColumn?: boolean
}) {
  if (rows.length === 0) {
    return <p className="text-sm text-slate-500">No data for the selected filters.</p>
  }

  return (
    <Table>
      <TableHead>
        <TableHeaderCell>Group</TableHeaderCell>
        <TableHeaderCell>Count</TableHeaderCell>
        {amountColumn ? <TableHeaderCell>Total amount</TableHeaderCell> : null}
      </TableHead>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.group}>
            <TableCell>{formatLabel(row.group)}</TableCell>
            <TableCell>{row.count}</TableCell>
            {amountColumn ? (
              <TableCell>{formatCurrency(row.total_amount_cents ?? 0)}</TableCell>
            ) : null}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

export function ReportDetailPage() {
  const { reportType: rawReportType } = useParams<{ reportType: string }>()
  const [, setSearchParams] = useSearchParams()
  const [isDownloading, setIsDownloading] = useState<'csv' | 'pdf' | null>(null)

  // Every hook below is called unconditionally, on every render, regardless
  // of whether the :reportType param is valid — the invalid case is handled
  // by the early return AFTER the hooks, not by skipping the hooks.
  const reportType = isReportType(rawReportType) ? rawReportType : undefined
  const defaultGroupBy = reportType ? defaultGroupByForReport(reportType) : ''
  const { data, isLoading, isError } = useReport(reportType)
  const reportMeta = REPORT_TYPE_OPTIONS.find((item) => item.value === reportType)

  const handleSearch = useCallback(
    (values: ReportSearchFormValues) => {
      const params = new URLSearchParams()
      setSearchParam(params, 'from_date', values.from_date)
      setSearchParam(params, 'to_date', values.to_date)
      setSearchParam(params, 'group_by', values.group_by)
      setSearchParams(params)
    },
    [setSearchParams],
  )

  const handleDownload = async (format: 'csv' | 'pdf') => {
    if (!reportType) return
    setIsDownloading(format)
    try {
      const params = new URLSearchParams(window.location.search)
      await downloadReport(reportType, {
        from_date: params.get('from_date')
          ? new Date(`${params.get('from_date')}T00:00:00`).toISOString()
          : undefined,
        to_date: params.get('to_date')
          ? new Date(`${params.get('to_date')}T23:59:59`).toISOString()
          : undefined,
        group_by: params.get('group_by') ?? defaultGroupBy,
      }, format)
    } finally {
      setIsDownloading(null)
    }
  }

  if (!reportType) {
    return <Navigate to="/reports" replace />
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Link to="/reports" className="text-sm font-medium text-brand-600 hover:text-brand-700">
            ← Back to reports
          </Link>
          <h1 className="mt-2 text-2xl font-semibold text-slate-900">{reportMeta?.label}</h1>
          <p className="mt-1 text-sm text-slate-500">{reportMeta?.description}</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            isLoading={isDownloading === 'csv'}
            onClick={() => void handleDownload('csv')}
          >
            Export CSV
          </Button>
          <Button
            variant="secondary"
            size="sm"
            isLoading={isDownloading === 'pdf'}
            onClick={() => void handleDownload('pdf')}
          >
            Export PDF
          </Button>
        </div>
      </div>

      <ReportSearchForm
        reportType={reportType}
        defaultGroupBy={defaultGroupBy}
        onSubmit={handleSearch}
      />

      {isLoading ? (
        <Card>
          <Spinner label="Running report…" />
        </Card>
      ) : null}

      {isError ? (
        <Card>
          <p className="text-sm text-red-600">Unable to load report data.</p>
        </Card>
      ) : null}

      {data && reportType === 'transactions' ? (
        <Card title="Results">
          <p className="mb-4 text-sm text-slate-500">
            Total: {(data as TransactionVolumeReport).total_count} transactions ·{' '}
            {formatCurrency((data as TransactionVolumeReport).total_amount_cents)}
          </p>
          <VolumeResultsTable
            rows={(data as TransactionVolumeReport).rows}
            amountColumn
          />
        </Card>
      ) : null}

      {data && (reportType === 'cases' || reportType === 'alerts') ? (
        <Card title="Results">
          <p className="mb-4 text-sm text-slate-500">
            Total: {(data as CaseVolumeReport | AlertVolumeReport).total_count}
          </p>
          <VolumeResultsTable rows={(data as CaseVolumeReport | AlertVolumeReport).rows} />
        </Card>
      ) : null}

      {data && reportType === 'sla' ? (
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Card className="p-4">
              <p className="text-xs uppercase text-slate-500">Closed</p>
              <p className="mt-1 text-2xl font-semibold">
                {(data as SlaPerformanceReport).total_closed}
              </p>
            </Card>
            <Card className="p-4">
              <p className="text-xs uppercase text-slate-500">Met SLA</p>
              <p className="mt-1 text-2xl font-semibold text-emerald-600">
                {(data as SlaPerformanceReport).met_sla}
              </p>
            </Card>
            <Card className="p-4">
              <p className="text-xs uppercase text-slate-500">Missed SLA</p>
              <p className="mt-1 text-2xl font-semibold text-amber-600">
                {(data as SlaPerformanceReport).missed_sla}
              </p>
            </Card>
            <Card className="p-4">
              <p className="text-xs uppercase text-slate-500">Compliance</p>
              <p className="mt-1 text-2xl font-semibold">
                {formatPercent((data as SlaPerformanceReport).compliance_rate)}
              </p>
            </Card>
          </div>
          <Card title="Breakdown by group">
            <Table>
              <TableHead>
                <TableHeaderCell>Group</TableHeaderCell>
                <TableHeaderCell>Closed</TableHeaderCell>
                <TableHeaderCell>Met SLA</TableHeaderCell>
                <TableHeaderCell>Missed SLA</TableHeaderCell>
              </TableHead>
              <TableBody>
                {(data as SlaPerformanceReport).breakdown.map((row) => (
                  <TableRow key={row.group}>
                    <TableCell>{formatLabel(row.group)}</TableCell>
                    <TableCell>{row.closed}</TableCell>
                    <TableCell>{row.met_sla}</TableCell>
                    <TableCell>{row.missed_sla}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </div>
      ) : null}

      <ScheduleReportForm reportType={reportType} />
    </div>
  )
}
