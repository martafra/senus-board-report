import { Badge } from '@/components/ui/badge'

export function ReportedBadge({ isActualReported }: { isActualReported: boolean }) {
  if (isActualReported) {
    return <Badge variant="default">Reported</Badge>
  }
  return (
    <Badge variant="outline" title="Estimated by splitting a reported total, not itself a reported figure">
      Modelled
    </Badge>
  )
}
