import type { ReactElement } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'
import { DebtInstrumentsPanel } from './DebtInstrumentsPanel'
import { TooltipProvider } from '@/components/ui/tooltip'
import * as api from '@/lib/api'

vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api')>('@/lib/api')
  return { ...actual, fetchDebtInstruments: vi.fn() }
})

function renderWithProviders(ui: ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>{ui}</TooltipProvider>
    </QueryClientProvider>,
  )
}

describe('DebtInstrumentsPanel', () => {
  it('badges a still-outstanding loan as Outstanding and a repaid one as Repaid, with the repayment detail behind a tooltip', async () => {
    vi.mocked(api.fetchDebtInstruments).mockResolvedValue([
      {
        name: 'SBCI backed term loan',
        principal: 100000,
        start_date: '2024-07-01',
        provider: 'SBCI',
        repaid_date: null,
        note: null,
      },
      {
        name: 'Working Capital Loan - Anthony Childs',
        principal: 100000,
        start_date: '2025-03-01',
        provider: 'Anthony Childs',
        repaid_date: '2025-10-31',
        note: 'Exact repayment day not disclosed; dated to the last day of the disclosed month.',
      },
    ])

    renderWithProviders(<DebtInstrumentsPanel />)

    expect(await screen.findByText('SBCI backed term loan')).toBeInTheDocument()
    expect(screen.getByText('Outstanding')).toBeInTheDocument()
    expect(screen.getByText('Repaid')).toBeInTheDocument()
    expect(screen.queryByText(/exact repayment day/i)).not.toBeInTheDocument()

    const user = userEvent.setup()
    await user.hover(screen.getByRole('button', { name: /when was this repaid/i }))

    expect(await screen.findByText(/repaid 31 oct 2025/i)).toBeInTheDocument()
  })
})
