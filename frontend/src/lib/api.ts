import { describeErrorDetail } from '@/lib/errors'
import type { TokenResponse } from '@/types/auth'

export class ApiError extends Error {
  status: number
  detail?: string

  constructor(message: string, status: number, detail?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

const API_BASE = import.meta.env.VITE_API_URL ?? '/api/v1'

type RequestOptions = {
  method?: string
  body?: unknown
  signal?: AbortSignal
  /** Skip attaching a bearer token and skip the refresh-on-401 flow — for /auth/login and /auth/refresh. */
  skipAuth?: boolean
}

// The access token lives in memory only, never in localStorage — it's the
// one place a stored XSS payload could otherwise read it back out. The
// refresh token never reaches JS at all: it's an httpOnly cookie the browser
// attaches automatically to same-site requests against its own scoped path.
let accessToken: string | null = null

export function setAccessToken(token: string | null): void {
  accessToken = token
}

export function getAccessToken(): string | null {
  return accessToken
}

let refreshPromise: Promise<void> | null = null
let sessionExpiredHandler: (() => void) | null = null

/**
 * Registered once by AuthProvider so that a 401 discovered by *any* query in
 * the app — not just the one checking the current session — can clear local
 * state and send the user back to /login instead of failing silently.
 */
export function setSessionExpiredHandler(handler: (() => void) | null): void {
  sessionExpiredHandler = handler
}

async function refreshAccessToken(): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    throw new ApiError('Session expired', response.status)
  }

  const tokens = (await response.json()) as TokenResponse
  setAccessToken(tokens.access_token)
}

/**
 * Every caller that needs a fresh access token — a 401 retry, or
 * AuthProvider's bootstrap-on-mount — awaits this SAME promise instead of
 * calling /auth/refresh itself. The backend's refresh token is single-use
 * and rotates on every call, so two concurrent refreshes would have the
 * second one fail by design (this is also what makes it safe against React
 * StrictMode double-invoking an effect that calls this on mount).
 */
export function ensureFreshToken(): Promise<void> {
  refreshPromise ??= refreshAccessToken().finally(() => {
    refreshPromise = null
  })
  return refreshPromise
}

async function rawFetch(path: string, options: RequestOptions): Promise<Response> {
  const headers: Record<string, string> = { Accept: 'application/json' }

  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  if (!options.skipAuth && accessToken) {
    headers.Authorization = `Bearer ${accessToken}`
  }

  return fetch(`${API_BASE}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    signal: options.signal,
    // Needed both ways: to send the httpOnly refresh cookie back on /auth/refresh
    // and /auth/logout, and to let the browser store it in the first place from
    // /auth/login's Set-Cookie — neither happens on a cross-origin request
    // without this, even though the cookie itself is same-site scoped.
    credentials: 'include',
  })
}

async function authFetch(path: string, options: RequestOptions, attempt = 0): Promise<Response> {
  const response = await rawFetch(path, options)

  if (response.status !== 401 || options.skipAuth) {
    return response
  }

  if (attempt === 0) {
    try {
      await ensureFreshToken()
    } catch {
      setAccessToken(null)
      sessionExpiredHandler?.()
      return response
    }
    return authFetch(path, options, attempt + 1)
  }

  setAccessToken(null)
  sessionExpiredHandler?.()
  return response
}

async function throwForResponse(response: Response): Promise<never> {
  let detail: string | undefined
  try {
    const problem = (await response.json()) as { detail?: unknown }
    // FastAPI's own 422 sends `detail` as an array of {loc, msg} objects, not
    // the string our problem+json handlers send. Flatten it here so no caller
    // ever ends up rendering an object as a React child.
    detail = describeErrorDetail(problem.detail)
  } catch {
    detail = undefined
  }
  throw new ApiError(detail ?? response.statusText, response.status, detail)
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await authFetch(path, options)

  if (!response.ok) {
    await throwForResponse(response)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

/** For endpoints that return a file (report CSV/PDF export) instead of JSON. */
export async function apiBlob(path: string, options: RequestOptions = {}): Promise<Blob> {
  const response = await authFetch(path, options)

  if (!response.ok) {
    await throwForResponse(response)
  }

  return response.blob()
}
