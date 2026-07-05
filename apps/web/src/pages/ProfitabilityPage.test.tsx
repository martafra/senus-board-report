import type { ReactElement } from 'react'
import { render, screen, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'
import { ProfitabilityPage } from './ProfitabilityPage'
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

// The page also renders an InsightPanel, which makes its own request; give it a resolved (if
// unused) response so these metrics-focused tests aren't left waiting on it too.
function mockInsightResolved() {
  vi.mocked(api.fetchInsight).mockResolvedValue({
    section_key: 'profitability',
    content: 'placeholder',
    model: 'gemini-2.5-flash',
    generated_at: '2026-07-04T12:00:00Z',
    prompt_version: 'v1',
  })
}

describe('ProfitabilityPage', () => {
  it('shows a loading state, then the fetched metrics', async () => {
    mockInsightResolved()
    vi.mocked(api.fetchMetrics).mockResolvedValue([
      {
        period_label: 'FY2025',
        period_type: 'ANNUAL',
        start_date: '2024-07-01',
        end_date: '2025-06-30',
        is_actual_reported: true,
        metrics: {
          gross_margin: { value: 77.5, unit: '%', description: 'Gross margin explanation' },
          ebitda: { value: -613313, unit: 'EUR', description: 'EBITDA explanation' },
        },
      },
    ])

    renderWithProviders(<ProfitabilityPage />)

    const table = await screen.findByRole('table')
    expect(await within(table).findByText('FY2025')).toBeInTheDocument()
    expect(within(table).getByText('77.5%')).toBeInTheDocument()
    expect(within(table).getByText('Reported')).toBeInTheDocument()
  })

  it('shows an error state when the request fails', async () => {
    mockInsightResolved()
    vi.mocked(api.fetchMetrics).mockRejectedValue(new Error('network error'))

    renderWithProviders(<ProfitabilityPage />)

    expect(await screen.findByText(/could not load this section/i)).toBeInTheDocument()
  })
})
