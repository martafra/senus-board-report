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

const ACCENT = 'var(--color-chart-3)'

const COLUMNS: MetricColumn[] = [
  { key: 'ebitda', label: 'EBITDA' },
  { key: 'free_cash_flow', label: 'Free Cash Flow' },
  { key: 'cash_runway_months', label: 'Cash Runway' },
  { key: 'working_capital', label: 'Working Capital' },
]

export function CashLiquidityPage() {
  const { data, isLoading, error } = useMetrics('cash-liquidity')

  return (
    <div className="flex flex-col gap-6">
      <SectionHeading color={ACCENT}>Cash & Liquidity</SectionHeading>
      <InsightPanel section="cash-liquidity" />
      <SectionState isLoading={isLoading} error={error} data={data}>
        {(periods) => {
          const chartData = periods.map((period) => ({
            period: period.period_label,
            free_cash_flow: period.metrics.free_cash_flow?.value ?? null,
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
                    <Bar dataKey="free_cash_flow" name="Free Cash Flow (EUR)" fill={ACCENT} />
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
