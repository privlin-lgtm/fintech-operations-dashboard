export type TokenResponse = {
  access_token: string
  refresh_token: string
  token_type: string
}

export type LoginCredentials = {
  email: string
  password: string
  mfa_code?: string
}

export type AuthSession = {
  accessToken: string
  refreshToken: string
}
