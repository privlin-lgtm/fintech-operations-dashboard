import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  fetchCurrentUser,
  login as loginRequest,
  logout as logoutRequest,
} from '@/features/auth/authApi'
import { ensureFreshToken, setAccessToken, setSessionExpiredHandler } from '@/lib/api'
import { authKeys } from '@/lib/queryKeys'
import type { LoginCredentials } from '@/types/auth'
import type { User } from '@/types/user'

// 'bootstrapping': we don't yet know if the httpOnly refresh cookie from a
// previous session is still good — nothing else can render until this
// resolves. 'authenticated'/'unauthenticated' are the settled states.
type SessionStatus = 'bootstrapping' | 'authenticated' | 'unauthenticated'

type AuthContextValue = {
  user: User | undefined
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<SessionStatus>('bootstrapping')

  // The API client calls this the moment ANY request's 401 can't be resolved
  // by a refresh — not just the /auth/me query below — so a session that
  // expires while the user is deep in a case detail page still recovers
  // cleanly instead of leaving every query on the page silently broken.
  const handleSessionExpired = useCallback(() => {
    setAccessToken(null)
    setStatus('unauthenticated')
    queryClient.clear()
  }, [queryClient])

  useEffect(() => {
    setSessionExpiredHandler(handleSessionExpired)
    return () => setSessionExpiredHandler(null)
  }, [handleSessionExpired])

  // On mount, trade whatever httpOnly refresh cookie the browser still has
  // for a fresh access token — this is what makes a session survive a page
  // reload, since the access token itself is never persisted anywhere.
  // Routed through the same single-flight ensureFreshToken() the 401-retry
  // path uses: React StrictMode double-invokes this effect in dev, and the
  // refresh token is single-use, so without sharing that lock the second
  // invocation's call would always lose the race and 401.
  useEffect(() => {
    let cancelled = false
    ensureFreshToken()
      .then(() => {
        if (cancelled) return
        setStatus('authenticated')
      })
      .catch(() => {
        if (cancelled) return
        setStatus('unauthenticated')
      })
    return () => {
      cancelled = true
    }
  }, [])

  const userQuery = useQuery({
    queryKey: authKeys.me(),
    queryFn: fetchCurrentUser,
    enabled: status === 'authenticated',
    retry: false,
  })

  const loginMutation = useMutation({
    mutationFn: loginRequest,
    onSuccess: (tokens) => {
      setAccessToken(tokens.access_token)
      setStatus('authenticated')
      void queryClient.invalidateQueries({ queryKey: authKeys.me() })
    },
  })

  const logoutMutation = useMutation({
    mutationFn: logoutRequest,
    onSettled: () => {
      setAccessToken(null)
      setStatus('unauthenticated')
      queryClient.clear()
    },
  })

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      await loginMutation.mutateAsync(credentials)
    },
    [loginMutation],
  )

  const logout = useCallback(async () => {
    await logoutMutation.mutateAsync()
  }, [logoutMutation])

  const value = useMemo<AuthContextValue>(
    () => ({
      user: userQuery.data,
      isAuthenticated: status === 'authenticated' && Boolean(userQuery.data),
      isLoading:
        status === 'bootstrapping' ||
        (status === 'authenticated' && userQuery.isLoading) ||
        loginMutation.isPending ||
        logoutMutation.isPending,
      login,
      logout,
    }),
    [
      status,
      login,
      loginMutation.isPending,
      logout,
      logoutMutation.isPending,
      userQuery.data,
      userQuery.isLoading,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
