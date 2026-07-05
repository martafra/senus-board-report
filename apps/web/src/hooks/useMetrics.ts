import { useQuery } from '@tanstack/react-query'
import { fetchMetrics, type MetricsSection } from '@/lib/api'

export function useMetrics(section: MetricsSection) {
  return useQuery({
    queryKey: ['metrics', section],
    queryFn: () => fetchMetrics(section),
  })
}
