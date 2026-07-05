import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, Tooltip as RechartsTooltip, XAxis, YAxis } from 'recharts'
import type { PeriodMetrics } from '@/lib/api'
import { formatEur } from '@/lib/format'

interface BridgeStep {
  name: string
  value: number
  isTotal: boolean
}

interface BridgeRow {
  name: string
  base: number
  barValue: number
  actual: number
  isTotal: boolean
}

function toWaterfallRows(steps: BridgeStep[]): BridgeRow[] {
  let cumulative = 0
  return steps.map((step) => {
    if (step.isTotal) {
      cumulative = step.value
      return { name: step.name, base: 0, barValue: step.value, actual: step.value, isTotal: true }
    }
    const from = cumulative
    cumulative += step.value
    return {
      name: step.name,
      base: Math.min(from, cumulative),
      barValue: Math.abs(step.value),
      actual: step.value,
      isTotal: false,
    }
  })
}

/**
 * The walk from EBITDA to Free Cash Flow for the most recent period with complete data: EBITDA
 * (a total bar from zero), then the working-capital/interest/tax adjustment and investing cash
 * flow (floating delta bars), landing on Free Cash Flow (another total bar from zero). By
 * construction the four figures sum consistently, so this is a reconciliation, not a new estimate.
 */
export function EbitdaToFcfBridge({ periods, color }: { periods: PeriodMetrics[]; color: string }) {
  const latest = [...periods]
    .reverse()
    .find(
      (period) =>
        period.metrics.ebitda &&
        period.metrics.operating_cash_adjustments &&
        period.metrics.cash_investing &&
        period.metrics.free_cash_flow,
    )

  if (!latest) {
    return null
  }

  const rows = toWaterfallRows([
    { name: 'EBITDA', value: latest.metrics.ebitda!.value, isTotal: true },
    {
      name: 'Working Capital & Other',
      value: latest.metrics.operating_cash_adjustments!.value,
      isTotal: false,
    },
    { name: 'Investing', value: latest.metrics.cash_investing!.value, isTotal: false },
    { name: 'Free Cash Flow', value: latest.metrics.free_cash_flow!.value, isTotal: true },
  ])

  return (
    <div className="h-64 rounded-lg border bg-background p-4">
      <p className="mb-2 text-xs text-muted-foreground">
        EBITDA to Free Cash Flow bridge, {latest.period_label}.
      </p>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={rows} margin={{ top: 20 }}>
          <XAxis dataKey="name" />
          <YAxis hide />
          <RechartsTooltip
            formatter={(_value, _name, item) => formatEur(item.payload.actual)}
            labelFormatter={(name) => name}
          />
          <Bar dataKey="base" stackId="bridge" fill="transparent" />
          <Bar dataKey="barValue" stackId="bridge">
            {rows.map((row) => (
              <Cell key={row.name} fill={color} fillOpacity={row.isTotal ? 1 : 0.5} />
            ))}
            <LabelList
              dataKey="actual"
              position="top"
              formatter={(value: unknown) => formatEur(value as number)}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
