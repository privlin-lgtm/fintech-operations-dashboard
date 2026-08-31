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

  const userQuery = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: () => fetchCurrentUser(getAccessToken()!),
    enabled: hasToken,
    retry: false,
  })

  useEffect(() => {
    if (userQuery.isError && hasToken) {
      clearTokens()
      setHasToken(false)
    }
  }, [hasToken, userQuery.isError])

  const loginMutation = useMutation({
    mutationFn: loginRequest,
    onSuccess: (tokens) => {
      setTokens(tokens.access_token, tokens.refresh_token)
      setHasToken(true)
      void queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
    },
  })

  const logoutMutation = useMutation({
    mutationFn: async () => {
      const refreshToken = getRefreshToken()
      const accessToken = getAccessToken()
      if (refreshToken && accessToken) {
        await logoutRequest(refreshToken, accessToken)
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
