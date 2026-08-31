export type TokenResponse = {
  access_token: string
  token_type: string
}

export type LoginCredentials = {
  email: string
  password: string
  mfa_code?: string
}
