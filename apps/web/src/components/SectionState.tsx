import type { ReactNode } from 'react'
import type { PeriodMetrics } from '@/lib/api'

/**
 * Shared loading/error/empty handling for a metrics section page, so each page only has to worry
 * about rendering its own chart and table once real data has arrived.
 */
export function SectionState({
  isLoading,
  error,
  data,
  children,
}: {
  isLoading: boolean
  error: unknown
  data: PeriodMetrics[] | undefined
  children: (data: PeriodMetrics[]) => ReactNode
}) {
  if (isLoading) {
    return <p className="text-muted-foreground">Loading...</p>
  }
  if (error) {
    return <p className="text-destructive">Could not load this section. Please try again.</p>
  }
  if (!data || data.length === 0) {
    return <p className="text-muted-foreground">No data available yet.</p>
  }
  return <>{children(data)}</>
}
