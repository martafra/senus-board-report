import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { SectionState } from '@/components/SectionState'
import { InfoTooltip } from '@/components/InfoTooltip'
import { useDebtInstruments } from '@/hooks/useDebtInstruments'
import { formatDate, formatEur } from '@/lib/format'

/**
 * The company's disclosed debt instruments, alongside the DSCR ratio: a repaid loan no longer
 * counts toward the company's debt service burden, so it's shown as Repaid rather than dropped
 * silently, to avoid a stale, since-repaid loan reading as if it's still outstanding.
 */
export function DebtInstrumentsPanel() {
  const { data, isLoading, error } = useDebtInstruments()

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Debt Instruments</CardTitle>
      </CardHeader>
      <CardContent>
        <SectionState isLoading={isLoading} error={error} data={data}>
          {(instruments) => (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Instrument</TableHead>
                  <TableHead>Principal</TableHead>
                  <TableHead>Drawn</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {instruments.map((instrument) => (
                  <TableRow key={instrument.name}>
                    <TableCell className="font-medium whitespace-normal">
                      {instrument.name}
                    </TableCell>
                    <TableCell>{formatEur(instrument.principal)}</TableCell>
                    <TableCell>{formatDate(instrument.start_date)}</TableCell>
                    <TableCell>
                      {instrument.repaid_date ? (
                        <span className="inline-flex items-center gap-1">
                          <Badge variant="outline">Repaid</Badge>
                          {instrument.note && (
                            <InfoTooltip
                              label="When was this repaid?"
                              text={`Repaid ${formatDate(instrument.repaid_date)}. ${instrument.note}`}
                            />
                          )}
                        </span>
                      ) : (
                        <Badge>Outstanding</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </SectionState>
      </CardContent>
    </Card>
  )
}
