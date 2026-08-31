export function buildQueryString(params: Record<string, string | number | undefined | null>): string {
  const search = new URLSearchParams()

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value))
    }
  }

  const query = search.toString()
  return query ? `?${query}` : ''
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return '—'
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export function formatLabel(value: string): string {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

export function formatCurrency(cents: number, currency = 'USD'): string {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency,
  }).format(cents / 100)
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return '—'
  }

  return `${(value * 100).toFixed(1)}%`
}

export function toIsoDateInput(value: string | null | undefined): string {
  if (!value) {
    return ''
  }

  return value.slice(0, 10)
}

export function dateInputToIso(value: string): string | undefined {
  if (!value) {
    return undefined
  }

  return new Date(`${value}T00:00:00`).toISOString()
}

export function dateInputToIsoEnd(value: string): string | undefined {
  if (!value) {
    return undefined
  }

  return new Date(`${value}T23:59:59`).toISOString()
}
