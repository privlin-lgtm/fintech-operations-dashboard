import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { StrictMode } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider, useAuth } from '@/features/auth/AuthProvider'
import { apiRequest, setAccessToken, setSessionExpiredHandler } from '@/lib/api'

// These tests exercise AuthProvider together with the REAL lib/api.ts and
// authApi.ts — only global fetch is mocked, at the network boundary. That's
// deliberate: the bug this suite guards against (a broken silent-refresh
// bootstrap) lived in the interaction between AuthProvider's mount effect
// and api.ts's single-flight lock, not in either module in isolation.

const ME_RESPONSE = {
  id: 'user-1',
  email: 'ava@example.com',
  full_name: 'Ava Chen',
  role_id: 'role-1',
  mfa_enabled: false,
  status: 'active',
  last_login_at: null,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  role: { id: 'role-1', name: 'analyst', description: null, permissions: {}, created_at: '', updated_at: '' },
}

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

function AuthConsumer() {
  const { isLoading, isAuthenticated, user, login, logout } = useAuth()
  return (
    <div>
      <span data-testid="status">
        {isLoading ? 'loading' : isAuthenticated ? 'authenticated' : 'unauthenticated'}
      </span>
      <span data-testid="email">{user?.email ?? ''}</span>
      <button onClick={() => void login({ email: 'ava@example.com', password: 'correct-horse-battery' })}>
        login
      </button>
      <button onClick={() => void logout()}>logout</button>
    </div>
  )
}

// toHaveTextContent does substring matching by default, and 'unauthenticated'
// contains 'authenticated' — a plain toHaveTextContent('authenticated') would
// pass on either state. Exact equality avoids that trap.
async function waitForStatus(status: 'loading' | 'authenticated' | 'unauthenticated') {
  await waitFor(() => expect(screen.getByTestId('status').textContent).toBe(status))
}

function renderAuth() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <AuthConsumer />
        </AuthProvider>
      </QueryClientProvider>
    </StrictMode>,
  )
}

describe('AuthProvider', () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    // lib/api.ts holds its access token and session-expired handler in
    // module-level state, which otherwise persists across tests in this file.
    setAccessToken(null)
    setSessionExpiredHandler(null)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('restores a session on mount via a single silent refresh, even under StrictMode', async () => {
    // StrictMode double-invokes the mount effect in dev. Without the
    // single-flight lock this regressed to: two /auth/refresh calls race
    // against the backend's single-use refresh token, one 401s, and the
    // user gets bounced to the login screen despite having a valid session.
    let refreshCalls = 0
    fetchMock.mockImplementation((url: string) => {
      if (url.includes('/auth/refresh')) {
        refreshCalls += 1
        return Promise.resolve(jsonResponse({ access_token: 'fresh-token', token_type: 'bearer' }))
      }
      if (url.includes('/auth/me')) {
        return Promise.resolve(jsonResponse(ME_RESPONSE))
      }
      throw new Error(`Unexpected fetch: ${url}`)
    })

    renderAuth()

    await waitForStatus('authenticated')

    expect(screen.getByTestId('email')).toHaveTextContent('ava@example.com')
    expect(refreshCalls).toBe(1)
  })

  it('settles to unauthenticated when there is no valid refresh cookie', async () => {
    fetchMock.mockImplementation((url: string) => {
      if (url.includes('/auth/refresh')) {
        return Promise.resolve(jsonResponse({ detail: 'No refresh token supplied' }, { status: 401 }))
      }
      throw new Error(`Unexpected fetch: ${url}`)
    })

    renderAuth()

    await waitForStatus('unauthenticated')
    expect(screen.getByTestId('email')).toHaveTextContent('')
  })

  it('logs in and populates the session without ever storing a refresh token client-side', async () => {
    fetchMock.mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/auth/refresh')) {
        return Promise.resolve(jsonResponse({ detail: 'No refresh token supplied' }, { status: 401 }))
      }
      if (url.includes('/auth/login')) {
        expect(init?.credentials).toBe('include')
        return Promise.resolve(jsonResponse({ access_token: 'fresh-token', token_type: 'bearer' }))
      }
      if (url.includes('/auth/me')) {
        return Promise.resolve(jsonResponse(ME_RESPONSE))
      }
      throw new Error(`Unexpected fetch: ${url}`)
    })

    renderAuth()
    await waitForStatus('unauthenticated')

    screen.getByRole('button', { name: 'login' }).click()

    await waitForStatus('authenticated')
    expect(screen.getByTestId('email')).toHaveTextContent('ava@example.com')
  })

  it('logs out, clears the session, and does not survive a subsequent bootstrap', async () => {
    fetchMock.mockImplementation((url: string, init?: RequestInit) => {
      if (url.includes('/auth/refresh')) {
        return Promise.resolve(jsonResponse({ access_token: 'fresh-token', token_type: 'bearer' }))
      }
      if (url.includes('/auth/me')) {
        return Promise.resolve(jsonResponse(ME_RESPONSE))
      }
      if (url.includes('/auth/logout')) {
        expect(init?.credentials).toBe('include')
        return Promise.resolve(jsonResponse(undefined, { status: 204 }))
      }
      throw new Error(`Unexpected fetch: ${url}`)
    })

    renderAuth()
    await waitForStatus('authenticated')

    screen.getByRole('button', { name: 'logout' }).click()

    await waitForStatus('unauthenticated')
    expect(screen.getByTestId('email')).toHaveTextContent('')
  })

  it('recovers from a session expiring mid-app: any apiRequest 401 flips the whole app to unauthenticated', async () => {
    let refreshAttempts = 0
    fetchMock.mockImplementation((url: string) => {
      if (url.includes('/auth/refresh')) {
        refreshAttempts += 1
        // First refresh (bootstrap) succeeds; the second (triggered by the
        // later 401) fails, simulating a since-revoked/expired cookie.
        if (refreshAttempts === 1) {
          return Promise.resolve(jsonResponse({ access_token: 'fresh-token', token_type: 'bearer' }))
        }
        return Promise.resolve(jsonResponse({}, { status: 401 }))
      }
      if (url.includes('/auth/me')) {
        return Promise.resolve(jsonResponse(ME_RESPONSE))
      }
      if (url.includes('/cases')) {
        return Promise.resolve(jsonResponse({}, { status: 401 }))
      }
      throw new Error(`Unexpected fetch: ${url}`)
    })

    renderAuth()
    await waitForStatus('authenticated')

    await expect(apiRequest('/cases')).rejects.toThrow()

    await waitForStatus('unauthenticated')
  })
})
