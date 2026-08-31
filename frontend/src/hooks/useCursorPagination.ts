import { useCallback, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

export function useCursorPagination(entityLabel: string) {
  const [searchParams, setSearchParams] = useSearchParams()
  const [cursorHistory, setCursorHistory] = useState<string[]>([])
  const currentCursor = searchParams.get('cursor')

  const resetPagination = useCallback(() => {
    setCursorHistory([])
  }, [])

  const applySearchParams = useCallback(
    (params: URLSearchParams) => {
      resetPagination()
      setSearchParams(params)
    },
    [resetPagination, setSearchParams],
  )

  const goNext = useCallback(
    (nextCursor: string | null | undefined) => {
      if (!nextCursor) {
        return
      }

      setCursorHistory((history) => [...history, currentCursor ?? ''])
      const params = new URLSearchParams(searchParams)
      params.set('cursor', nextCursor)
      setSearchParams(params)
    },
    [currentCursor, searchParams, setSearchParams],
  )

  const goPrevious = useCallback(() => {
    if (cursorHistory.length === 0) {
      return
    }

    const previousCursor = cursorHistory[cursorHistory.length - 1]
    setCursorHistory((history) => history.slice(0, -1))

    const params = new URLSearchParams(searchParams)
    if (previousCursor) {
      params.set('cursor', previousCursor)
    } else {
      params.delete('cursor')
    }
    setSearchParams(params)
  }, [cursorHistory, searchParams, setSearchParams])

  const summary = useCallback(
    (count: number) => {
      const page = cursorHistory.length + 1
      const label = count === 1 ? entityLabel : `${entityLabel}s`
      return `Page ${page} · Showing ${count} ${label}`
    },
    [cursorHistory.length, entityLabel],
  )

  const pageNumber = useMemo(() => cursorHistory.length + 1, [cursorHistory.length])

  return {
    applySearchParams,
    goNext,
    goPrevious,
    hasPrevious: cursorHistory.length > 0,
    pageNumber,
    resetPagination,
    summary,
  }
}

export function setSearchParam(
  params: URLSearchParams,
  key: string,
  value: string | boolean | undefined | null,
) {
  if (value === undefined || value === null || value === '') {
    params.delete(key)
    return
  }

  if (typeof value === 'boolean') {
    if (value) {
      params.set(key, 'true')
    }
    return
  }

  params.set(key, value)
}
