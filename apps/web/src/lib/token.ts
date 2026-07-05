// A thin wrapper around localStorage so the token has one place it's read/written from, shared
// between the API client and the auth context without either importing the other.
const STORAGE_KEY = 'senus_token'

export function getToken(): string | null {
  return localStorage.getItem(STORAGE_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(STORAGE_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(STORAGE_KEY)
}
