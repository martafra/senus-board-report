import type { ReactElement } from 'react'
import { render, screen, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'
import { CashLiquidityPage } from './CashLiquidityPage'
import { TooltipProvider } from '@/components/ui/tooltip'
import * as api from '@/lib/api'

vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api')>('@/lib/api')
  return { ...actual, fetchMetrics: vi.fn(), fetchInsight: vi.fn() }
})

function renderWithProviders(ui: ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>{ui}</TooltipProvider>
    </QueryClientProvider>,
  )
}

function mockInsightResolved() {
  vi.mocked(api.fetchInsight).mockResolvedValue({
    section_key: 'cash-liquidity',
    content: 'placeholder',
    model: 'gemini-2.5-flash',
    generated_at: '2026-07-04T12:00:00Z',
    prompt_version: 'v1',
  })
}

describe('CashLiquidityPage', () => {
  it('shows the metrics table and the EBITDA to FCF bridge for the latest period', async () => {
    mockInsightResolved()
    vi.mocked(api.fetchMetrics).mockResolvedValue([
      {
        period_label: 'FY2025',
        period_type: 'ANNUAL',
        start_date: '2024-07-01',
        end_date: '2025-06-30',
        is_actual_reported: true,
        metrics: {
          ebitda: { value: -613313, unit: 'EUR', description: 'EBITDA' },
          operating_cash_adjustments: { value: 218112, unit: 'EUR', description: 'Adjustments' },
          cash_investing: { value: -3451, unit: 'EUR', description: 'Investing' },
          free_cash_flow: { value: -398652, unit: 'EUR', description: 'FCF' },
        },
      },
    ])

    renderWithProviders(<CashLiquidityPage />)

    const table = await screen.findByRole('table')
    expect(within(table).getByText('FY2025')).toBeInTheDocument()
    expect(screen.getByText(/ebitda to free cash flow bridge, fy2025/i)).toBeInTheDocument()
  })
})
