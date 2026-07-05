import type { MetricValue } from '@/lib/api'

const eurFormatter = new Intl.NumberFormat('en-IE', {
  style: 'currency',
  currency: 'EUR',
  maximumFractionDigits: 0,
})

export function formatEur(value: number): string {
  return eurFormatter.format(value)
}

/** For an ISO date string (no time component), e.g. "2030-06-30" -> "30 Jun 2030". */
export function formatDate(isoDate: string): string {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString('en-IE', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function formatMetricValue(metric: MetricValue): string {
  switch (metric.unit) {
    case 'EUR':
      return eurFormatter.format(metric.value)
    case '%':
      return `${metric.value.toFixed(1)}%`
    case 'x':
      return `${metric.value.toFixed(2)}x`
    case 'count':
      return metric.value.toLocaleString('en-IE')
  }
}

/** For a Recharts <Tooltip formatter>, whose value type isn't guaranteed to be a plain number. */
export function formatTooltipNumber(value: unknown): string {
  return typeof value === 'number' ? value.toLocaleString('en-IE') : String(value)
}
