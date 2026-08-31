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

  it('case:close is restricted to investigator, team_lead, and admin', () => {
    expect(roleHasPermission('investigator', 'case:close')).toBe(true)
    expect(roleHasPermission('team_lead', 'case:close')).toBe(true)
    expect(roleHasPermission('admin', 'case:close')).toBe(true)
    expect(roleHasPermission('analyst', 'case:close')).toBe(false)
    expect(roleHasPermission('compliance_auditor', 'case:close')).toBe(false)
  })

  it('case:reassign is restricted to team_lead and admin', () => {
    expect(roleHasPermission('team_lead', 'case:reassign')).toBe(true)
    expect(roleHasPermission('admin', 'case:reassign')).toBe(true)
    expect(roleHasPermission('analyst', 'case:reassign')).toBe(false)
    expect(roleHasPermission('investigator', 'case:reassign')).toBe(false)
    expect(roleHasPermission('compliance_auditor', 'case:reassign')).toBe(false)
  })

  it('alert:assign, alert:escalate, and alert:resolve exclude analyst and compliance_auditor', () => {
    for (const permission of ['alert:assign', 'alert:escalate', 'alert:resolve'] as const) {
      expect(roleHasPermission('investigator', permission)).toBe(true)
      expect(roleHasPermission('team_lead', permission)).toBe(true)
      expect(roleHasPermission('admin', permission)).toBe(true)
      expect(roleHasPermission('analyst', permission)).toBe(false)
      expect(roleHasPermission('compliance_auditor', permission)).toBe(false)
    }
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
