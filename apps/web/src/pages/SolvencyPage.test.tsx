import type { ReactElement } from 'react'
import { render, screen, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'
import { SolvencyPage } from './SolvencyPage'
import { TooltipProvider } from '@/components/ui/tooltip'
import * as api from '@/lib/api'

vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api')>('@/lib/api')
  return {
    ...actual,
    fetchMetrics: vi.fn(),
    fetchInsight: vi.fn(),
    fetchDebtInstruments: vi.fn(),
  }
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
// unused) response so this test isn't left waiting on it too.
function mockInsightResolved() {
  vi.mocked(api.fetchInsight).mockResolvedValue({
    section_key: 'solvency',
    content: 'placeholder',
    model: 'gemini-2.5-flash',
    generated_at: '2026-07-04T12:00:00Z',
    prompt_version: 'v1',
  })
}

describe('SolvencyPage', () => {
  it('shows the DSCR table alongside the debt instruments panel', async () => {
    mockInsightResolved()
    vi.mocked(api.fetchMetrics).mockResolvedValue([
      {
        period_label: 'FY2025',
        period_type: 'ANNUAL',
        start_date: '2024-07-01',
        end_date: '2025-06-30',
        is_actual_reported: true,
        metrics: {
          dscr: { value: 5.2, unit: 'x', description: 'DSCR explanation' },
        },
      },
    ])
    vi.mocked(api.fetchDebtInstruments).mockResolvedValue([
      {
        name: 'SBCI backed term loan',
        principal: 100000,
        start_date: '2024-07-01',
        provider: 'SBCI',
        repaid_date: null,
        note: null,
      },
    ])

    renderWithProviders(<SolvencyPage />)

    await screen.findByText('SBCI backed term loan')
    const tables = screen.getAllByRole('table')
    const dscrTable = tables.find((table) => within(table).queryByText('FY2025'))
    const debtTable = tables.find((table) => within(table).queryByText('SBCI backed term loan'))

    expect(dscrTable).toBeDefined()
    expect(debtTable).toBeDefined()
    expect(within(debtTable!).getByText('Outstanding')).toBeInTheDocument()
  })
})
