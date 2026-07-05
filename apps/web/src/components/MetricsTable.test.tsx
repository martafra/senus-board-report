import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { MetricsTable } from './MetricsTable'
import { TooltipProvider } from '@/components/ui/tooltip'
import type { PeriodMetrics } from '@/lib/api'

const DATA: PeriodMetrics[] = [
  {
    period_label: 'FY2024',
    period_type: 'ANNUAL',
    start_date: '2023-07-01',
    end_date: '2024-06-30',
    is_actual_reported: true,
    metrics: {
      revenue: { value: 688317, unit: 'EUR', description: 'Revenue explanation' },
    },
  },
]

describe('MetricsTable', () => {
  it('shows a dash with an explanatory tooltip when a period has no value for a column', async () => {
    render(
      <TooltipProvider>
        <MetricsTable
          data={DATA}
          columns={[
            { key: 'revenue', label: 'Revenue' },
            { key: 'yoy_growth', label: 'YoY Growth' },
          ]}
        />
      </TooltipProvider>,
    )

    expect(screen.getByText('€688,317')).toBeInTheDocument()
    expect(screen.getByText('-')).toBeInTheDocument()
    expect(screen.queryByText(/was not disclosed/i)).not.toBeInTheDocument()

    const user = userEvent.setup()
    await user.hover(screen.getByRole('button', { name: /why is this missing/i }))

    expect(
      await screen.findByText(/yoy growth was not disclosed for fy2024/i),
    ).toBeInTheDocument()
  })
})
