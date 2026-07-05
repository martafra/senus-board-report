import type { PeriodMetrics } from '@/lib/api'
import { formatMetricValue } from '@/lib/format'
import { ReportedBadge } from '@/components/ReportedBadge'
import { InfoTooltip } from '@/components/InfoTooltip'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

export interface MetricColumn {
  key: string
  label: string
}

/**
 * One row per period, one column per metric. A column's info tooltip is taken from whichever
 * period actually has that metric (descriptions are the same everywhere it appears), so the
 * header still explains itself even for periods missing that particular figure.
 */
export function MetricsTable({
  data,
  columns,
}: {
  data: PeriodMetrics[]
  columns: MetricColumn[]
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Period</TableHead>
          {columns.map((column) => {
            const description = data.find((period) => period.metrics[column.key])?.metrics[
              column.key
            ]?.description
            return (
              <TableHead key={column.key}>
                <span className="inline-flex items-center gap-1">
                  {column.label}
                  {description && <InfoTooltip text={description} />}
                </span>
              </TableHead>
            )
          })}
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((period) => (
          <TableRow key={period.period_label}>
            <TableCell className="font-medium">
              <span className="inline-flex items-center gap-2">
                {period.period_label}
                <ReportedBadge isActualReported={period.is_actual_reported} />
              </span>
            </TableCell>
            {columns.map((column) => {
              const metric = period.metrics[column.key]
              return (
                <TableCell key={column.key}>{metric ? formatMetricValue(metric) : '-'}</TableCell>
              )
            })}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
