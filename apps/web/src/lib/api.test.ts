import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiGet, login } from './api'
import { clearToken, setToken } from './token'

describe('api client', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    clearToken()
  })

  it('attaches the bearer token when one is stored', async () => {
    setToken('my-token')
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await apiGet('/some/path')

    const [, options] = fetchMock.mock.calls[0]
    expect((options.headers as Headers).get('Authorization')).toBe('Bearer my-token')
  })

  it('does not attach a token when none is stored', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    await apiGet('/some/path')

    const [, options] = fetchMock.mock.calls[0]
    expect((options.headers as Headers).has('Authorization')).toBe(false)
  })

  it('throws an ApiError with the backend detail message on failure', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Incorrect email or password' }), {
        status: 401,
        statusText: 'Unauthorized',
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiGet('/auth/me')).rejects.toMatchObject({
      message: 'Incorrect email or password',
      status: 401,
    })
  })

  it('sends login credentials as form-encoded data, not JSON', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ access_token: 'tok', token_type: 'bearer' }), {
        status: 200,
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await login('ceo@senus.com', 's3cret')

    const [, options] = fetchMock.mock.calls[0]
    expect(options.body).toBeInstanceOf(URLSearchParams)
    expect((options.body as URLSearchParams).get('username')).toBe('ceo@senus.com')
  })
})
