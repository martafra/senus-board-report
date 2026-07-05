import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import { LandingPage } from './LandingPage'
import { AuthProvider } from '@/context/AuthContext'
import { clearToken, setToken } from '@/lib/token'

function renderLanding() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<p>dashboard page</p>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('LandingPage', () => {
  beforeEach(() => {
    clearToken()
  })

  it('shows the hero and a Sign in button when not authenticated', () => {
    renderLanding()
    expect(
      screen.getByText('One place to actually understand how Senus PLC is doing'),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('opens the sign in dialog in place, without navigating away, when clicked', async () => {
    const user = userEvent.setup()
    renderLanding()

    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    // the hero content is still there underneath, we never left the landing page
    expect(
      screen.getByText('One place to actually understand how Senus PLC is doing'),
    ).toBeInTheDocument()
  })

  it('redirects straight to the dashboard when already authenticated', async () => {
    setToken('some-token')
    renderLanding()

    expect(await screen.findByText('dashboard page')).toBeInTheDocument()
  })
})
