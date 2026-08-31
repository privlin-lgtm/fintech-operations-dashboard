import { apiRequest } from '@/lib/api'
import type { LoginCredentials, TokenResponse } from '@/types/auth'
import type { User } from '@/types/user'

export async function login(credentials: LoginCredentials): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    body: credentials,
  })
}

export async function fetchCurrentUser(token: string): Promise<User> {
  return apiRequest<User>('/auth/me', { token })
}

export async function logout(refreshToken: string, accessToken: string): Promise<void> {
  await apiRequest<void>('/auth/logout', {
    method: 'POST',
    token: accessToken,
    body: { refresh_token: refreshToken },
  })
}
