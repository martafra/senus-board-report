import { createContext, useCallback, useState, type ReactNode } from 'react'
import { login as apiLogin } from '@/lib/api'
import { clearToken, getToken, setToken } from '@/lib/token'

interface AuthContextValue {
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(() => getToken() !== null)

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await apiLogin(email, password)
    setToken(access_token)
    setIsAuthenticated(true)
  }, [])

  const logout = useCallback(() => {
    clearToken()
    setIsAuthenticated(false)
  }, [])

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
