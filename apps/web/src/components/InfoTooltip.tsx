import { Info } from 'lucide-react'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

/**
 * A small "i" icon that shows a plain-language explanation on hover, focus or tap, so a number can
 * be understood without needing a finance background. Triggers on focus (not just hover) so it's
 * reachable by keyboard and works on touch devices.
 */
export function InfoTooltip({
  text,
  label = 'What does this mean?',
}: {
  text: string
  label?: string
}) {
  return (
    <Tooltip>
      <TooltipTrigger
        aria-label={label}
        className="inline-flex cursor-help text-muted-foreground hover:text-foreground"
      >
        <Info className="size-3.5" />
      </TooltipTrigger>
      <TooltipContent className="max-w-64">{text}</TooltipContent>
    </Tooltip>
  )
}
