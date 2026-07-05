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
import { InfoTooltip } from '@/components/InfoTooltip'
import { KPITargetsPanel } from '@/components/KPITargetsPanel'
import { SectionHeading } from '@/components/SectionHeading'
import { formatTooltipNumber } from '@/lib/format'

const ACCENT = 'var(--color-chart-1)'

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
      <SectionHeading color={ACCENT}>Growth & Revenue</SectionHeading>
      <InsightPanel section="growth" />
      <KPITargetsPanel />
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
                <p className="mb-2 flex items-center gap-1 text-xs text-muted-foreground">
                  Monthly revenue trend.
                  <InfoTooltip
                    label="Why is this modelled?"
                    text="Modelled: split from reported annual/half-year totals, not itself reported month by month."
                  />
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
                      stroke={ACCENT}
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
