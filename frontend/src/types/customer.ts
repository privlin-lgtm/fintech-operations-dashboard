import type { Account } from '@/types/account'
import type { Alert } from '@/types/alert'
import type { Case } from '@/types/case'

export type CustomerStatus = 'active' | 'suspended' | 'closed'
export type RiskTier = 'low' | 'medium' | 'high'
export type KycStatus = 'unverified' | 'pending' | 'verified' | 'rejected'

export type CustomerSortField =
  | 'created_at'
  | '-created_at'
  | 'updated_at'
  | '-updated_at'
  | 'full_name'
  | '-full_name'
  | 'risk_tier'
  | '-risk_tier'
  | 'status'
  | '-status'
  | 'kyc_status'
  | '-kyc_status'

export type Customer = {
  id: string
  full_name: string
  email: string | null
  phone: string | null
  kyc_status: KycStatus
  risk_tier: RiskTier
  status: CustomerStatus
  created_at: string
  updated_at: string
}

export type CustomerProfile = Customer & {
  account_count: number
  open_case_count: number
  total_case_count: number
  open_alert_count: number
  recent_accounts: Account[]
  recent_cases: Case[]
  recent_alerts: Alert[]
}

export type CustomerSearchParams = {
  q?: string
  status?: CustomerStatus
  risk_tier?: RiskTier
  kyc_status?: KycStatus
  sort?: CustomerSortField
  limit?: number
  cursor?: string
}

export type CustomerSearchFormValues = {
  q: string
  status: '' | CustomerStatus
  risk_tier: '' | RiskTier
  kyc_status: '' | KycStatus
  sort: CustomerSortField
}

export const CUSTOMER_STATUS_OPTIONS: { label: string; value: CustomerStatus }[] = [
  { label: 'Active', value: 'active' },
  { label: 'Suspended', value: 'suspended' },
  { label: 'Closed', value: 'closed' },
]

export const RISK_TIER_OPTIONS: { label: string; value: RiskTier }[] = [
  { label: 'Low', value: 'low' },
  { label: 'Medium', value: 'medium' },
  { label: 'High', value: 'high' },
]

export const KYC_STATUS_OPTIONS: { label: string; value: KycStatus }[] = [
  { label: 'Unverified', value: 'unverified' },
  { label: 'Pending', value: 'pending' },
  { label: 'Verified', value: 'verified' },
  { label: 'Rejected', value: 'rejected' },
]

export const CUSTOMER_SORT_OPTIONS: { label: string; value: CustomerSortField }[] = [
  { label: 'Newest first', value: '-created_at' },
  { label: 'Oldest first', value: 'created_at' },
  { label: 'Name A–Z', value: 'full_name' },
  { label: 'Name Z–A', value: '-full_name' },
  { label: 'Risk tier', value: 'risk_tier' },
  { label: 'Status', value: 'status' },
]
