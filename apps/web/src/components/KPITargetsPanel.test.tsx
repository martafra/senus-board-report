import type { ReactElement } from 'react'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'
import { KPITargetsPanel } from './KPITargetsPanel'
import * as api from '@/lib/api'

vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api')>('@/lib/api')
  return { ...actual, fetchKPITargets: vi.fn() }
})

function renderWithProviders(ui: ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('KPITargetsPanel', () => {
  it('shows each disclosed target with its description and date', async () => {
    vi.mocked(api.fetchKPITargets).mockResolvedValue([
      {
        name: 'Revenue CAGR',
        target_value: 50,
        target_date: '2030-06-30',
        description: 'Target: at least 50% compound annual growth rate of revenue.',
      },
    ])

    renderWithProviders(<KPITargetsPanel />)

    expect(await screen.findByText(/revenue cagr/i)).toBeInTheDocument()
    expect(
      screen.getByText('Target: at least 50% compound annual growth rate of revenue.'),
    ).toBeInTheDocument()
    expect(screen.getByText(/by 30 jun 2030/i)).toBeInTheDocument()
  })

  it('shows an error state when the request fails', async () => {
    vi.mocked(api.fetchKPITargets).mockRejectedValue(new Error('network error'))

    renderWithProviders(<KPITargetsPanel />)

    expect(await screen.findByText(/could not load this section/i)).toBeInTheDocument()
  })
})
