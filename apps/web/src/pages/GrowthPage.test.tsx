import type { ReactElement } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'
import { GrowthPage } from './GrowthPage'
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
// unused) response so this chart-focused test isn't left waiting on it too.
function mockInsightResolved() {
  vi.mocked(api.fetchInsight).mockResolvedValue({
    section_key: 'growth',
    content: 'placeholder',
    model: 'gemini-2.5-flash',
    generated_at: '2026-07-04T12:00:00Z',
    prompt_version: 'v1',
  })
}

describe('GrowthPage', () => {
  it('shows the monthly chart caption and reveals the modelled explanation only on hover', async () => {
    mockInsightResolved()
    vi.mocked(api.fetchMetrics).mockResolvedValue([
      {
        period_label: 'Jan 2025',
        period_type: 'MONTHLY',
        start_date: '2025-01-01',
        end_date: '2025-01-31',
        is_actual_reported: false,
        metrics: {
          revenue: { value: 50000, unit: 'EUR', description: 'Revenue' },
        },
      },
    ])

    renderWithProviders(<GrowthPage />)

    expect(await screen.findByText('Monthly revenue trend.')).toBeInTheDocument()
    expect(screen.queryByText(/split from reported annual/i)).not.toBeInTheDocument()

    const user = userEvent.setup()
    await user.hover(screen.getByRole('button', { name: /why is this modelled/i }))

    expect(
      await screen.findByText(/split from reported annual\/half-year totals/i),
    ).toBeInTheDocument()
  })
})
