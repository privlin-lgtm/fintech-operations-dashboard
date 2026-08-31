import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'

export function ForgotPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-brand-700 px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center text-white">
          <h1 className="text-3xl font-semibold">Reset your password</h1>
          <p className="mt-2 text-sm text-slate-300">
            Enter your work email and we&apos;ll send reset instructions.
          </p>
        </div>

        <Card title="Password recovery">
          <form
            className="space-y-4"
            onSubmit={(event) => {
              event.preventDefault()
            }}
          >
            <Input label="Email" type="email" autoComplete="email" required />
            <p className="text-sm text-slate-500">
              Password reset is not wired to the API yet. This page is ready for the auth flow.
            </p>
            <div className="flex items-center justify-between gap-3">
              <Link
                to="/login"
                className="text-sm font-medium text-brand-600 hover:text-brand-700"
              >
                Back to sign in
              </Link>
              <Button type="submit">Send reset link</Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  )
}
