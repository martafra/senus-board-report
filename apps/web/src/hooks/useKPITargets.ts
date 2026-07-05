import { useQuery } from '@tanstack/react-query'
import { fetchKPITargets } from '@/lib/api'

export function useKPITargets() {
  return useQuery({
    queryKey: ['kpi-targets'],
    queryFn: fetchKPITargets,
  })
}
