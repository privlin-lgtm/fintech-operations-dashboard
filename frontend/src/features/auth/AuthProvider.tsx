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

import { fetchCurrentUser, login as loginRequest, logout as logoutRequest } from '@/features/auth/authApi'
import { setSessionExpiredHandler } from '@/lib/api'
import { authKeys } from '@/lib/queryKeys'
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from '@/lib/storage'
import type { LoginCredentials } from '@/types/auth'
import type { User } from '@/types/user'

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
  const [hasToken, setHasToken] = useState(() => Boolean(getAccessToken()))

  // The API client calls this the moment ANY request's 401 can't be resolved
  // by a refresh — not just the /auth/me query below — so a session that
  // expires while the user is deep in a case detail page still recovers
  // cleanly instead of leaving every query on the page silently broken.
  const handleSessionExpired = useCallback(() => {
    setHasToken(false)
    queryClient.clear()
  }, [queryClient])

  useEffect(() => {
    setSessionExpiredHandler(handleSessionExpired)
    return () => setSessionExpiredHandler(null)
  }, [handleSessionExpired])

  const userQuery = useQuery({
    queryKey: authKeys.me(),
    queryFn: fetchCurrentUser,
    enabled: hasToken,
    retry: false,
  })

  const loginMutation = useMutation({
    mutationFn: loginRequest,
    onSuccess: (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token)
      setHasToken(true)
      void queryClient.invalidateQueries({ queryKey: authKeys.me() })
    },
  })

  const logoutMutation = useMutation({
    mutationFn: async () => {
      const refreshToken = getRefreshToken()
      if (refreshToken) {
        await logoutRequest(refreshToken)
      }
    },
    onSettled: () => {
      clearTokens()
      setHasToken(false)
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
      isAuthenticated: hasToken && Boolean(userQuery.data),
      isLoading:
        (hasToken && userQuery.isLoading) ||
        loginMutation.isPending ||
        logoutMutation.isPending,
      login,
      logout,
    }),
    [
      hasToken,
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
