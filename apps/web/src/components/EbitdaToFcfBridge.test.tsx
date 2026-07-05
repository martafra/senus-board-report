import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { EbitdaToFcfBridge } from './EbitdaToFcfBridge'
import type { PeriodMetrics } from '@/lib/api'

function period(overrides: PeriodMetrics['metrics']): PeriodMetrics {
  return {
    period_label: 'FY2025',
    period_type: 'ANNUAL',
    start_date: '2024-07-01',
    end_date: '2025-06-30',
    is_actual_reported: true,
    metrics: overrides,
  }
}

describe('EbitdaToFcfBridge', () => {
  it('renders the bridge for the latest period with all four figures present', () => {
    const periods = [
      period({}), // an earlier period missing the bridge figures, should be skipped
      period({
        ebitda: { value: -613313, unit: 'EUR', description: 'EBITDA' },
        operating_cash_adjustments: { value: 218112, unit: 'EUR', description: 'Adjustments' },
        cash_investing: { value: -3451, unit: 'EUR', description: 'Investing' },
        free_cash_flow: { value: -398652, unit: 'EUR', description: 'FCF' },
      }),
    ]

    render(<EbitdaToFcfBridge periods={periods} color="#eda100" />)

    expect(screen.getByText(/ebitda to free cash flow bridge, fy2025/i)).toBeInTheDocument()
  })

  it('renders nothing when no period has the complete set of bridge figures', () => {
    const periods = [period({ ebitda: { value: -613313, unit: 'EUR', description: 'EBITDA' } })]

    const { container } = render(<EbitdaToFcfBridge periods={periods} color="#eda100" />)

    expect(container).toBeEmptyDOMElement()
  })
})
