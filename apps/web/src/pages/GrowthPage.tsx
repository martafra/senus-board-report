import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useMetrics } from '@/hooks/useMetrics'
import { SectionState } from '@/components/SectionState'
import { MetricsTable, type MetricColumn } from '@/components/MetricsTable'
import { InsightPanel } from '@/components/InsightPanel'
import { formatTooltipNumber } from '@/lib/format'

const COLUMNS: MetricColumn[] = [
  { key: 'revenue', label: 'Revenue' },
  { key: 'yoy_growth', label: 'YoY Growth' },
  { key: 'customers_enterprise', label: 'Enterprise Customers' },
  { key: 'customers_independent', label: 'Independent Customers' },
  { key: 'customers_rd', label: 'R&D Customers' },
  { key: 'new_customers_period_enterprise', label: 'New Enterprise Customers' },
  { key: 'new_bookings_value_period', label: 'New Bookings' },
  { key: 'open_pipeline_value', label: 'Open Pipeline' },
]

export function GrowthPage() {
  const { data, isLoading, error } = useMetrics('growth')

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-semibold">Growth & Revenue</h2>
      <InsightPanel section="growth" />
      <SectionState isLoading={isLoading} error={error} data={data}>
        {(periods) => {
          const monthly = periods.filter((period) => period.period_type === 'MONTHLY')
          const reportedPeriods = periods.filter((period) => period.period_type !== 'MONTHLY')
          const chartData = monthly.map((period) => ({
            period: period.period_label,
            revenue: period.metrics.revenue?.value ?? null,
          }))
          return (
            <>
              <div className="h-64 rounded-lg border bg-background p-4">
                <p className="mb-2 text-xs text-muted-foreground">
                  Monthly revenue trend. Modelled: split from reported annual/half-year totals, not
                  itself reported month by month.
                </p>
                <ResponsiveContainer width="100%" height="85%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" hide />
                    <YAxis />
                    <RechartsTooltip formatter={formatTooltipNumber} />
                    <Line
                      type="monotone"
                      dataKey="revenue"
                      name="Revenue (EUR)"
                      stroke="var(--color-primary)"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <MetricsTable data={reportedPeriods} columns={COLUMNS} />
            </>
          )
        }}
      </SectionState>
    </div>
  )
}
