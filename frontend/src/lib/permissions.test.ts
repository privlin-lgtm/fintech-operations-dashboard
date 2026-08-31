import { describe, expect, it } from 'vitest'

import { PERMISSIONS, roleHasPermission } from '@/lib/permissions'

describe('roleHasPermission', () => {
  it('allows a role listed for the permission', () => {
    expect(roleHasPermission('admin', 'customer:write')).toBe(true)
    expect(roleHasPermission('team_lead', 'customer:write')).toBe(true)
  })

  it('denies a role not listed for the permission', () => {
    expect(roleHasPermission('analyst', 'customer:write')).toBe(false)
    expect(roleHasPermission('investigator', 'customer:write')).toBe(false)
    expect(roleHasPermission('compliance_auditor', 'customer:write')).toBe(false)
  })

  it('denies a missing role (null or undefined)', () => {
    expect(roleHasPermission(null, 'customer:read')).toBe(false)
    expect(roleHasPermission(undefined, 'customer:read')).toBe(false)
  })

  it('denies an unrecognized role name', () => {
    expect(roleHasPermission('made_up_role', 'customer:read')).toBe(false)
  })

  it('report:schedule is restricted to team_lead, compliance_auditor, and admin', () => {
    expect(roleHasPermission('team_lead', 'report:schedule')).toBe(true)
    expect(roleHasPermission('compliance_auditor', 'report:schedule')).toBe(true)
    expect(roleHasPermission('admin', 'report:schedule')).toBe(true)
    expect(roleHasPermission('analyst', 'report:schedule')).toBe(false)
    expect(roleHasPermission('investigator', 'report:schedule')).toBe(false)
  })

  it('every *:read permission is open to all five backend roles', () => {
    const allRoles = ['analyst', 'investigator', 'team_lead', 'compliance_auditor', 'admin']
    const readPermissions = Object.keys(PERMISSIONS).filter((key) => key.endsWith(':read')) as (keyof typeof PERMISSIONS)[]

    for (const permission of readPermissions) {
      for (const role of allRoles) {
        expect(roleHasPermission(role, permission)).toBe(true)
      }
    }
  })
})
