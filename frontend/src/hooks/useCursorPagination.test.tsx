import { act, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { setSearchParam, useCursorPagination } from '@/hooks/useCursorPagination'

function wrapper({ children }: { children: ReactNode }) {
  return <MemoryRouter initialEntries={['/cases']}>{children}</MemoryRouter>
}

describe('useCursorPagination', () => {
  it('starts on page 1 with no previous page', () => {
    const { result } = renderHook(() => useCursorPagination('case'), { wrapper })

    expect(result.current.hasPrevious).toBe(false)
    expect(result.current.summary(3)).toBe('Page 1 · Showing 3 cases')
  })

  it('pluralizes the entity label based on count', () => {
    const { result } = renderHook(() => useCursorPagination('case'), { wrapper })

    expect(result.current.summary(1)).toBe('Page 1 · Showing 1 case')
  })

  it('goNext advances the page and enables previous', () => {
    const { result } = renderHook(() => useCursorPagination('case'), { wrapper })

    act(() => result.current.goNext('cursor-a'))

    expect(result.current.hasPrevious).toBe(true)
    expect(result.current.summary(5)).toBe('Page 2 · Showing 5 cases')
  })

  it('goNext does nothing without a cursor', () => {
    const { result } = renderHook(() => useCursorPagination('case'), { wrapper })

    act(() => result.current.goNext(null))
    act(() => result.current.goNext(undefined))

    expect(result.current.hasPrevious).toBe(false)
  })

  it('goPrevious pops back to the prior page', () => {
    const { result } = renderHook(() => useCursorPagination('case'), { wrapper })

    act(() => result.current.goNext('cursor-a'))
    act(() => result.current.goNext('cursor-b'))
    expect(result.current.summary(1).startsWith('Page 3')).toBe(true)

    act(() => result.current.goPrevious())
    expect(result.current.summary(1).startsWith('Page 2')).toBe(true)
    expect(result.current.hasPrevious).toBe(true)

    act(() => result.current.goPrevious())
    expect(result.current.summary(1).startsWith('Page 1')).toBe(true)
    expect(result.current.hasPrevious).toBe(false)
  })

  it('goPrevious does nothing on page 1', () => {
    const { result } = renderHook(() => useCursorPagination('case'), { wrapper })

    act(() => result.current.goPrevious())

    expect(result.current.hasPrevious).toBe(false)
    expect(result.current.summary(1).startsWith('Page 1')).toBe(true)
  })

  it('applySearchParams (a new search) resets the page history', () => {
    const { result } = renderHook(() => useCursorPagination('case'), { wrapper })

    act(() => result.current.goNext('cursor-a'))
    expect(result.current.hasPrevious).toBe(true)

    act(() => result.current.applySearchParams(new URLSearchParams({ status: 'new' })))

    expect(result.current.hasPrevious).toBe(false)
    expect(result.current.summary(1).startsWith('Page 1')).toBe(true)
  })
})

describe('setSearchParam', () => {
  it('sets a non-empty string value', () => {
    const params = new URLSearchParams()
    setSearchParam(params, 'q', 'ada')
    expect(params.get('q')).toBe('ada')
  })

  it('deletes the key for undefined, null, or empty string', () => {
    for (const value of [undefined, null, '']) {
      const params = new URLSearchParams({ q: 'existing' })
      setSearchParam(params, 'q', value)
      expect(params.has('q')).toBe(false)
    }
  })

  it('sets "true" only when the boolean is true, otherwise omits the key', () => {
    const paramsTrue = new URLSearchParams()
    setSearchParam(paramsTrue, 'sla_risk', true)
    expect(paramsTrue.get('sla_risk')).toBe('true')

    const paramsFalse = new URLSearchParams()
    setSearchParam(paramsFalse, 'sla_risk', false)
    expect(paramsFalse.has('sla_risk')).toBe(false)
  })
})
