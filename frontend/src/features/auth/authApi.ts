import { apiRequest } from '@/lib/api'
import type { LoginCredentials, TokenResponse } from '@/types/auth'
import type { User } from '@/types/user'

export async function login(credentials: LoginCredentials): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    body: credentials,
    skipAuth: true,
  })
}

export async function fetchCurrentUser(): Promise<User> {
  return apiRequest<User>('/auth/me')
}

export async function logout(refreshToken: string): Promise<void> {
  await apiRequest<void>('/auth/logout', {
    method: 'POST',
    body: { refresh_token: refreshToken },
  })
}
