import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { SectionState } from '@/components/SectionState'
import { useKPITargets } from '@/hooks/useKPITargets'
import { formatDate } from '@/lib/format'

/**
 * Senus's own disclosed 2030 strategic targets, shown alongside actual performance so a reader
 * can judge progress against the company's stated goals, not just against last year.
 */
export function KPITargetsPanel() {
  const { data, isLoading, error } = useKPITargets()

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Senus 2030 Targets</CardTitle>
      </CardHeader>
      <CardContent>
        <SectionState isLoading={isLoading} error={error} data={data}>
          {(targets) => (
            <ul className="flex flex-col gap-3">
              {targets.map((target) => (
                <li key={target.name} className="flex flex-col gap-0.5 text-sm">
                  <span className="font-medium">
                    {target.name} <span className="text-muted-foreground">by {formatDate(target.target_date)}</span>
                  </span>
                  <span className="text-muted-foreground">{target.description}</span>
                </li>
              ))}
            </ul>
          )}
        </SectionState>
      </CardContent>
    </Card>
  )
}
