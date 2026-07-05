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

const COLUMNS: MetricColumn[] = [{ key: 'roce', label: 'ROCE' }]

export function ReturnsPage() {
  const { data, isLoading, error } = useMetrics('returns')

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-semibold">Returns</h2>
      <InsightPanel section="returns" />
      <SectionState isLoading={isLoading} error={error} data={data}>
        {(periods) => {
          const chartData = periods.map((period) => ({
            period: period.period_label,
            roce: period.metrics.roce?.value ?? null,
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
                    <Bar dataKey="roce" name="ROCE (%)" fill="var(--color-primary)" />
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
