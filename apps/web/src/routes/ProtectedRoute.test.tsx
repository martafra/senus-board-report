import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { ProtectedRoute } from './ProtectedRoute'
import { AuthProvider } from '@/context/AuthContext'
import { clearToken, setToken } from '@/lib/token'

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<p>landing page</p>} />
          <Route path="/dashboard" element={<ProtectedRoute />}>
            <Route index element={<p>dashboard page</p>} />
          </Route>
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

describe('ProtectedRoute', () => {
  it('redirects to the landing page, not a separate login page, when not authenticated', () => {
    clearToken()
    renderAt('/dashboard')

    expect(screen.getByText('landing page')).toBeInTheDocument()
  })

  it('renders the protected content when authenticated', () => {
    setToken('some-token')
    renderAt('/dashboard')

    expect(screen.getByText('dashboard page')).toBeInTheDocument()
  })
})
