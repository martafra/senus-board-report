import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchInsight, regenerateInsight, type MetricsSection } from '@/lib/api'

export function useInsight(section: MetricsSection) {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ['insight', section],
    queryFn: () => fetchInsight(section),
  })
  const regenerate = useMutation({
    mutationFn: () => regenerateInsight(section),
    onSuccess: (data) => {
      queryClient.setQueryData(['insight', section], data)
    },
  })

  return { ...query, regenerate }
}
