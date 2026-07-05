import type { ReactNode } from 'react'

/**
 * Shared loading/error/empty handling for any list-shaped section of the dashboard, so each
 * consumer only has to worry about rendering its own content once real data has arrived.
 */
export function SectionState<T>({
  isLoading,
  error,
  data,
  children,
}: {
  isLoading: boolean
  error: unknown
  data: T[] | undefined
  children: (data: T[]) => ReactNode
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
