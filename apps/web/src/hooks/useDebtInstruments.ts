import { useQuery } from '@tanstack/react-query'
import { fetchDebtInstruments } from '@/lib/api'

export function useDebtInstruments() {
  return useQuery({
    queryKey: ['debt-instruments'],
    queryFn: fetchDebtInstruments,
  })
}
