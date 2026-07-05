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

const COLUMNS: MetricColumn[] = [{ key: 'dscr', label: 'DSCR' }]

export function SolvencyPage() {
  const { data, isLoading, error } = useMetrics('solvency')

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-semibold">Solvency & Leverage</h2>
      <InsightPanel section="solvency" />
      <p className="text-xs text-muted-foreground">
        Only shown for full financial years: half-year releases haven't disclosed the loan
        repayment schedule this ratio needs.
      </p>
      <SectionState isLoading={isLoading} error={error} data={data}>
        {(periods) => {
          const chartData = periods.map((period) => ({
            period: period.period_label,
            dscr: period.metrics.dscr?.value ?? null,
          }))
          return (
            <>
              <div className="h-64 rounded-lg border bg-background p-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <RechartsTooltip />
                    <Bar dataKey="dscr" name="DSCR (x)" fill="var(--color-primary)" />
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
