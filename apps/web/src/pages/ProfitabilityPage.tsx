import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useMetrics } from '@/hooks/useMetrics'
import { SectionState } from '@/components/SectionState'
import { MetricsTable, type MetricColumn } from '@/components/MetricsTable'
import { InsightPanel } from '@/components/InsightPanel'
import { SectionHeading } from '@/components/SectionHeading'
import { formatTooltipNumber } from '@/lib/format'

const ACCENT = 'var(--color-chart-2)'

const COLUMNS: MetricColumn[] = [
  { key: 'gross_margin', label: 'Gross Margin' },
  { key: 'operating_margin', label: 'Operating Margin' },
  { key: 'ebitda', label: 'EBITDA' },
  { key: 'ebitda_margin', label: 'EBITDA Margin' },
  { key: 'cost_of_sales', label: 'Cost of Sales' },
  { key: 'admin_expenses', label: 'Admin Expenses' },
  { key: 'distribution_costs', label: 'Distribution Costs' },
]

export function ProfitabilityPage() {
  const { data, isLoading, error } = useMetrics('profitability')

  return (
    <div className="flex flex-col gap-6">
      <SectionHeading color={ACCENT}>Profitability</SectionHeading>
      <InsightPanel section="profitability" />
      <SectionState isLoading={isLoading} error={error} data={data}>
        {(periods) => {
          const chartData = periods.map((period) => ({
            period: period.period_label,
            ebitda: period.metrics.ebitda?.value ?? null,
          }))
          return (
            <>
              <div className="h-64 rounded-lg border bg-background p-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <RechartsTooltip formatter={formatTooltipNumber} />
                    <Bar dataKey="ebitda" name="EBITDA (EUR)" fill={ACCENT} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <MetricsTable data={periods} columns={COLUMNS} />
            </>
          )
        }}
      </SectionState>
    </div>
  )
}
