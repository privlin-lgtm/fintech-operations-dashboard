import type { FormEvent } from 'react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/features/auth/AuthProvider'
import { ApiError } from '@/lib/api'

export function LoginPage() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      await login({ email, password })
    } catch (err) {
      const message =
        err instanceof ApiError ? err.detail ?? 'Invalid email or password.' : 'Sign in failed.'
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-brand-700 px-4">
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
          <form className="space-y-4" onSubmit={(event) => void handleSubmit(event)}>
            <Input
              label="Email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
            <Input
              label="Password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />

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
              <Button type="submit" isLoading={isSubmitting}>
                Sign in
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  )
}
