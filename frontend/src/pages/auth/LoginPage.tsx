import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/features/auth/AuthProvider'
import { ApiError } from '@/lib/api'

type LoginFormValues = {
  email: string
  password: string
  mfa_code: string
}

const MFA_REQUIRED_DETAIL = 'MFA code required'

export function LoginPage() {
  const { login } = useAuth()
  const [needsMfaCode, setNeedsMfaCode] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { register, handleSubmit, getValues, formState } = useForm<LoginFormValues>({
    defaultValues: { email: '', password: '', mfa_code: '' },
  })

  const onSubmit = handleSubmit(async (values) => {
    setError(null)
    try {
      await login({
        email: values.email,
        password: values.password,
        mfa_code: values.mfa_code || undefined,
      })
    } catch (err) {
      if (err instanceof ApiError && err.detail === MFA_REQUIRED_DETAIL) {
        // Not an error to show — the password was correct, we just need a
        // second factor now. Reveal the field and let the analyst resubmit.
        setNeedsMfaCode(true)
        return
      }
      const message =
        err instanceof ApiError ? (err.detail ?? 'Invalid email or password.') : 'Sign in failed.'
      setError(message)
    }
  })

  return (
    <div className="flex min-h-screen items-center justify-center bg-linear-to-br from-slate-900 via-slate-800 to-brand-700 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center text-white">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-brand-100">
            Fintech Ops
          </p>
          <h1 className="mt-2 text-3xl font-semibold">Sign in to your workspace</h1>
          <p className="mt-2 text-sm text-slate-300">
            Monitor cases, alerts, and operational risk in one place.
          </p>
        </div>

        <Card title="Account access">
          <form
            data-testid="login-form"
            className="space-y-4"
            onSubmit={(event) => void onSubmit(event)}
          >
            <Input
              label="Email"
              type="email"
              autoComplete="email"
              disabled={needsMfaCode}
              required
              data-testid="login-email"
              {...register('email', { required: true })}
            />
            <Input
              label="Password"
              type="password"
              autoComplete="current-password"
              disabled={needsMfaCode}
              required
              data-testid="login-password"
              {...register('password', { required: true })}
            />

            {needsMfaCode ? (
              <div>
                <Input
                  label="Authenticator code"
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  placeholder="6-digit code"
                  required
                  {...register('mfa_code', { required: true })}
                />
                <p className="mt-1.5 text-sm text-slate-500">
                  {getValues('email')} has an authenticator app enabled. Enter the current code to
                  finish signing in.
                </p>
              </div>
            ) : null}

            {error ? (
              <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
            ) : null}

            <div className="flex items-center justify-between gap-3">
              <Link
                to="/forgot-password"
                className="text-sm font-medium text-brand-600 hover:text-brand-700"
              >
                Forgot password?
              </Link>
              <Button type="submit" isLoading={formState.isSubmitting} data-testid="login-submit">
                {needsMfaCode ? 'Verify and sign in' : 'Sign in'}
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  )
}
