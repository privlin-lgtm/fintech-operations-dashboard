import type { ReactNode } from 'react'

type BadgeTone = 'default' | 'success' | 'warning' | 'danger' | 'info'

type BadgeProps = {
  children: ReactNode
  tone?: BadgeTone
}

const toneClasses: Record<BadgeTone, string> = {
  default: 'bg-slate-100 text-slate-700',
  success: 'bg-emerald-50 text-emerald-700',
  warning: 'bg-amber-50 text-amber-700',
  danger: 'bg-red-50 text-red-700',
  info: 'bg-blue-50 text-blue-700',
}

export function Badge({ children, tone = 'default' }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${toneClasses[tone]}`}
    >
      {children}
    </span>
  )
}

export function customerStatusTone(status: string): BadgeTone {
  switch (status) {
    case 'active':
      return 'success'
    case 'suspended':
      return 'warning'
    case 'closed':
      return 'default'
    default:
      return 'default'
  }
}

export function riskTierTone(riskTier: string): BadgeTone {
  switch (riskTier) {
    case 'high':
      return 'danger'
    case 'medium':
      return 'warning'
    case 'low':
      return 'success'
    default:
      return 'default'
  }
}

export function kycStatusTone(kycStatus: string): BadgeTone {
  switch (kycStatus) {
    case 'verified':
      return 'success'
    case 'pending':
      return 'info'
    case 'rejected':
      return 'danger'
    default:
      return 'default'
  }
}
