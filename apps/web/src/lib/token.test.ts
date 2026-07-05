import { beforeEach, describe, expect, it } from 'vitest'
import { clearToken, getToken, setToken } from './token'

describe('token storage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('returns null when nothing has been stored', () => {
    expect(getToken()).toBeNull()
  })

  it('returns the token that was set', () => {
    setToken('abc123')
    expect(getToken()).toBe('abc123')
  })

  it('returns null again after clearing', () => {
    setToken('abc123')
    clearToken()
    expect(getToken()).toBeNull()
  })
})
