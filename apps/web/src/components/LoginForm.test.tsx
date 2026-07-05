import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { LoginForm } from './LoginForm'
import { AuthProvider } from '@/context/AuthContext'
import * as api from '@/lib/api'

vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api')>('@/lib/api')
  return { ...actual, login: vi.fn() }
})

function renderForm(onSuccess = vi.fn()) {
  render(
    <AuthProvider>
      <LoginForm onSuccess={onSuccess} />
    </AuthProvider>,
  )
  return onSuccess
}

describe('LoginForm', () => {
  it('calls onSuccess after a successful login', async () => {
    vi.mocked(api.login).mockResolvedValue({ access_token: 'tok', token_type: 'bearer' })
    const onSuccess = renderForm()
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/email/i), 'ceo@senus.com')
    await user.type(screen.getByLabelText(/password/i), 's3cret')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(onSuccess).toHaveBeenCalled()
  })

  it('shows an error message and does not call onSuccess when login fails', async () => {
    vi.mocked(api.login).mockRejectedValue(new Error('Incorrect email or password'))
    const onSuccess = renderForm()
    const user = userEvent.setup()

    await user.type(screen.getByLabelText(/email/i), 'ceo@senus.com')
    await user.type(screen.getByLabelText(/password/i), 'wrong')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText(/something went wrong/i)).toBeInTheDocument()
    expect(onSuccess).not.toHaveBeenCalled()
  })
})
