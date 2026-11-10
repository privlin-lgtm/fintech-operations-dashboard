import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, apiRequest, getAccessToken, setAccessToken, setSessionExpiredHandler } from '@/lib/api'

function jsonResponse(body: unknown, init: { status?: number } = {}): Response {
  const status = init.status ?? 200
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: '',
    json: async () => body,
    blob: async () => new Blob([JSON.stringify(body)]),
  } as Response
}

describe('lib/api', () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    setAccessToken(null)
    setSessionExpiredHandler(null)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('attaches the in-memory access token as a bearer header', async () => {
    setAccessToken('token-abc')
    fetchMock.mockResolvedValueOnce(jsonResponse({ ok: true }))

    await apiRequest('/customers')

    const init = fetchMock.mock.calls[0][1] as RequestInit
    const headers = init.headers as Record<string, string>
    expect(headers.Authorization).toBe('Bearer token-abc')
  })

  it('omits the Authorization header for skipAuth requests', async () => {
    setAccessToken('token-abc')
    fetchMock.mockResolvedValueOnce(jsonResponse({ access_token: 'new', token_type: 'bearer' }))

    await apiRequest('/auth/login', { method: 'POST', body: { email: 'a@b.com' }, skipAuth: true })

    const init = fetchMock.mock.calls[0][1] as RequestInit
    const headers = init.headers as Record<string, string>
    expect(headers.Authorization).toBeUndefined()
  })

  it('always sends credentials: include, so the httpOnly refresh cookie can transport', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ ok: true }))

    await apiRequest('/customers')

    const init = fetchMock.mock.calls[0][1] as RequestInit
    expect(init.credentials).toBe('include')
  })

  it('refreshes once on a 401 and retries the original request with the new token', async () => {
    setAccessToken('stale-token')
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ detail: 'expired' }, { status: 401 })) // original
      .mockResolvedValueOnce(jsonResponse({ access_token: 'fresh-token', token_type: 'bearer' })) // refresh
      .mockResolvedValueOnce(jsonResponse({ id: '1' })) // retry

    const result = await apiRequest('/customers/1')

    expect(result).toEqual({ id: '1' })
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(fetchMock.mock.calls[1][0] as string).toContain('/auth/refresh')
    expect(getAccessToken()).toBe('fresh-token')
    const retryInit = fetchMock.mock.calls[2][1] as RequestInit
    const retryHeaders = retryInit.headers as Record<string, string>
    expect(retryHeaders.Authorization).toBe('Bearer fresh-token')
  })

  it('clears the session and notifies once when refresh itself fails', async () => {
    const handler = vi.fn()
    setSessionExpiredHandler(handler)
    setAccessToken('stale-token')
    fetchMock
      .mockResolvedValueOnce(jsonResponse({}, { status: 401 })) // original
      .mockResolvedValueOnce(jsonResponse({ detail: 'no refresh cookie' }, { status: 401 })) // refresh fails

    await expect(apiRequest('/customers/1')).rejects.toBeInstanceOf(ApiError)

    expect(handler).toHaveBeenCalledTimes(1)
    expect(getAccessToken()).toBeNull()
  })

  it('does not loop when the post-refresh retry 401s again', async () => {
    const handler = vi.fn()
    setSessionExpiredHandler(handler)
    setAccessToken('stale-token')
    fetchMock
      .mockResolvedValueOnce(jsonResponse({}, { status: 401 })) // original
      .mockResolvedValueOnce(jsonResponse({ access_token: 'fresh', token_type: 'bearer' })) // refresh succeeds
      .mockResolvedValueOnce(jsonResponse({}, { status: 401 })) // retry still 401s

    await expect(apiRequest('/customers/1')).rejects.toBeInstanceOf(ApiError)

    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(handler).toHaveBeenCalledTimes(1)
    expect(getAccessToken()).toBeNull()
  })

  it('never attempts a refresh for a 401 from a skipAuth request', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: 'bad credentials' }, { status: 401 }))

    await expect(
      apiRequest('/auth/login', { method: 'POST', body: {}, skipAuth: true }),
    ).rejects.toBeInstanceOf(ApiError)

    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('shares a single in-flight refresh across concurrent 401s', async () => {
    // This is the exact regression class that shipped broken: two callers
    // hitting a 401 at once must not fire two independent /auth/refresh
    // calls, since the backend's refresh token is single-use and the loser
    // of that race would 401 for real.
    setAccessToken('stale-token')
    const callCounts: Record<string, number> = {}

    fetchMock.mockImplementation((url: string) => {
      if (url.includes('/auth/refresh')) {
        callCounts.refresh = (callCounts.refresh ?? 0) + 1
        return Promise.resolve(jsonResponse({ access_token: 'fresh-token', token_type: 'bearer' }))
      }
      callCounts[url] = (callCounts[url] ?? 0) + 1
      const status = callCounts[url] === 1 ? 401 : 200
      return Promise.resolve(jsonResponse({ ok: true }, { status }))
    })

    const [a, b] = await Promise.all([apiRequest('/a'), apiRequest('/b')])

    expect(a).toEqual({ ok: true })
    expect(b).toEqual({ ok: true })
    expect(callCounts.refresh).toBe(1)
  })

  it('resolves 204 responses to undefined', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(undefined, { status: 204 }))

    const result = await apiRequest('/auth/logout', { method: 'POST' })

    expect(result).toBeUndefined()
  })

  it('surfaces the problem+json detail on ApiError', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ title: 'Conflict', detail: 'Email already exists' }, { status: 409 }),
    )

    const error = await apiRequest('/customers').catch((err: unknown) => err)

    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).status).toBe(409)
    expect((error as ApiError).detail).toBe('Email already exists')
  })

  it('flattens a FastAPI 422 validation array into a string detail', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(
        { detail: [{ type: 'uuid_parsing', loc: ['body', 'owner_id'], msg: 'Input should be a valid UUID' }] },
        { status: 422 },
      ),
    )

    const error = await apiRequest('/cases/abc/reassign', { method: 'POST', body: {} }).catch(
      (err: unknown) => err,
    )

    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).status).toBe(422)
    expect((error as ApiError).detail).toBe('Owner id: Input should be a valid UUID')
    expect((error as ApiError).message).toBe('Owner id: Input should be a valid UUID')
  })
})
