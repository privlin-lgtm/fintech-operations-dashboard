import { describe, expect, it } from 'vitest'

import { formatRoleName, formatUserRef } from '@/lib/format'

describe('formatRoleName', () => {
  it('turns a snake_case role into sentence case', () => {
    expect(formatRoleName('team_lead')).toBe('Team lead')
  })

  it('capitalises a single-word role', () => {
    expect(formatRoleName('analyst')).toBe('Analyst')
  })

  it('handles more than one underscore', () => {
    expect(formatRoleName('compliance_review_officer')).toBe('Compliance review officer')
  })
})

describe('formatUserRef', () => {
  it('shows the display name when the API resolved one', () => {
    expect(formatUserRef('Ava Chen', '3f1c2a9e-0000-4000-8000-000000000001')).toBe('Ava Chen')
  })

  it('shows Unassigned when there is no user id', () => {
    expect(formatUserRef(null, null)).toBe('Unassigned')
  })

  it('falls back to the id only when no name came back', () => {
    expect(formatUserRef(null, 'user-id')).toBe('user-id')
  })
})
