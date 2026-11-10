import { describe, expect, it } from 'vitest'

import { ApiError } from '@/lib/api'
import { describeErrorDetail, errorMessage } from '@/lib/errors'

// The body FastAPI sends for a request that fails validation, e.g. a non-UUID owner_id.
const fastApi422Detail = [
  {
    type: 'uuid_parsing',
    loc: ['body', 'owner_id'],
    msg: 'Input should be a valid UUID, invalid character: expected an optional prefix of `urn:uuid:` followed by [0-9a-fA-F-], found `n` at 1',
    input: 'not-a-uuid',
  },
]

describe('describeErrorDetail', () => {
  it('passes a string detail through', () => {
    expect(describeErrorDetail('Cannot reassign a closed case')).toBe('Cannot reassign a closed case')
  })

  it('flattens a FastAPI validation array into one sentence naming the field', () => {
    expect(describeErrorDetail(fastApi422Detail)).toMatch(/^Owner id: Input should be a valid UUID/)
  })

  it('joins several issues', () => {
    expect(
      describeErrorDetail([
        { loc: ['body', 'owner_id'], msg: 'Field required' },
        { loc: ['body', 'reason'], msg: 'Field required' },
      ]),
    ).toBe('Owner id: Field required; Reason: Field required')
  })

  it('returns undefined for shapes with nothing readable', () => {
    expect(describeErrorDetail(undefined)).toBeUndefined()
    expect(describeErrorDetail(null)).toBeUndefined()
    expect(describeErrorDetail({ unexpected: true })).toBeUndefined()
    expect(describeErrorDetail([])).toBeUndefined()
    expect(describeErrorDetail('   ')).toBeUndefined()
  })
})

describe('errorMessage', () => {
  it('returns null when there is no error', () => {
    expect(errorMessage(null)).toBeNull()
    expect(errorMessage(undefined)).toBeNull()
  })

  it('uses an ApiError detail', () => {
    expect(errorMessage(new ApiError('Conflict', 409, 'Cannot reassign a closed case'))).toBe(
      'Cannot reassign a closed case',
    )
  })

  it('always returns a string, even if an array detail slips through', () => {
    const raw = Object.assign(new Error('Unprocessable Entity'), { detail: fastApi422Detail })
    const message = errorMessage(raw)
    expect(typeof message).toBe('string')
    expect(message).toMatch(/^Owner id: Input should be a valid UUID/)
  })

  it('falls back to the message, then to a generic sentence', () => {
    expect(errorMessage(new Error('Network down'))).toBe('Network down')
    expect(errorMessage({})).toBe('Something went wrong.')
    expect(errorMessage(42)).toBe('Something went wrong.')
  })
})
