import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '@/lib/storage'
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
  /** Skip attaching a bearer token and skip the refresh-on-401 flow — for /auth/login. */
  skipAuth?: boolean
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
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    throw new ApiError('No refresh token available', 401)
  }

  const response = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  if (!response.ok) {
    throw new ApiError('Session expired', response.status)
  }

  const tokens = (await response.json()) as TokenResponse
  setTokens(tokens.access_token, tokens.refresh_token)
}

/**
 * Every caller that hits a 401 awaits this SAME promise instead of calling
 * /auth/refresh itself — the backend's refresh token is single-use and
 * rotates on every call, so two concurrent refreshes would have the second
 * one fail by design.
 */
function ensureFreshToken(): Promise<void> {
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

  if (!options.skipAuth) {
    const token = getAccessToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
  }

  return fetch(`${API_BASE}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    signal: options.signal,
  })
}

async function authFetch(path: string, options: RequestOptions, attempt = 0): Promise<Response> {
  const response = await rawFetch(path, options)

  if (response.status !== 401 || options.skipAuth) {
    return response
  }

  if (attempt === 0 && getRefreshToken()) {
    try {
      await ensureFreshToken()
    } catch {
      clearTokens()
      sessionExpiredHandler?.()
      return response
    }
    return authFetch(path, options, attempt + 1)
  }

  clearTokens()
  sessionExpiredHandler?.()
  return response
}

async function throwForResponse(response: Response): Promise<never> {
  let detail: string | undefined
  try {
    const problem = (await response.json()) as { detail?: string }
    detail = problem.detail
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
