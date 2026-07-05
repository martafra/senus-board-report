import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from './AuthContext'
import { useAuth } from '@/hooks/useAuth'
import { clearToken, getToken } from '@/lib/token'
import * as api from '@/lib/api'

vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api')>('@/lib/api')
  return { ...actual, login: vi.fn() }
})

function TestConsumer() {
  const { isAuthenticated, login: doLogin, logout } = useAuth()
  return (
    <div>
      <p>{isAuthenticated ? 'authenticated' : 'anonymous'}</p>
      <button onClick={() => doLogin('ceo@senus.com', 's3cret')}>login</button>
      <button onClick={logout}>logout</button>
    </div>
  )
}

describe('AuthProvider', () => {
  beforeEach(() => {
    clearToken()
    vi.mocked(api.login).mockReset()
  })

  it('starts unauthenticated when there is no stored token', () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    )
    expect(screen.getByText('anonymous')).toBeInTheDocument()
  })

  it('becomes authenticated and stores the token after a successful login', async () => {
    vi.mocked(api.login).mockResolvedValue({ access_token: 'new-token', token_type: 'bearer' })
    const user = userEvent.setup()
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    )

    await user.click(screen.getByText('login'))

    expect(await screen.findByText('authenticated')).toBeInTheDocument()
    expect(getToken()).toBe('new-token')
  })

  it('clears the token and becomes unauthenticated on logout', async () => {
    vi.mocked(api.login).mockResolvedValue({ access_token: 'new-token', token_type: 'bearer' })
    const user = userEvent.setup()
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    )
    await user.click(screen.getByText('login'))
    await screen.findByText('authenticated')

    await user.click(screen.getByText('logout'))

    expect(screen.getByText('anonymous')).toBeInTheDocument()
    expect(getToken()).toBeNull()
  })
})
