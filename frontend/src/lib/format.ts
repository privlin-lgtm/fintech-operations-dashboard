import { CASE_TYPE_OPTIONS } from '@/types/case'

/**
 * Validates a URL param against a known set of allowed values instead of
 * blindly `as`-casting it. A hand-edited or bookmarked URL with `?status=bogus`
 * is silently dropped (falls back to "no filter") rather than trusted as if
 * it were a real, narrow union value.
 */
export function parseEnumParam<T extends string>(
  value: string | null,
  allowed: readonly T[],
): T | undefined {
  return value !== null && (allowed as readonly string[]).includes(value) ? (value as T) : undefined
}

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

/** snake_case identifiers ("activity_explained") as sentence-case words ("Activity explained"). */
export function formatSentenceCase(value: string): string {
  const spaced = value.replace(/_/g, ' ').replace(/\s+/g, ' ').trim()
  return spaced.charAt(0).toUpperCase() + spaced.slice(1).toLowerCase()
}

/** Role names are snake_case identifiers ("team_lead"); show them in sentence case ("Team lead"). */
export function formatRoleName(value: string): string {
  return formatSentenceCase(value)
}

/** Case types use their form labels ("aml_review" → "AML review"); unknown ones fall back to sentence case. */
export function formatCaseType(value: string): string {
  return CASE_TYPE_OPTIONS.find((option) => option.value === value)?.label ?? formatSentenceCase(value)
}

/** Resolution codes are free-text snake_case ("activity_explained" → "Activity explained"). */
export function formatResolutionCode(value: string | null | undefined): string {
  return value ? formatSentenceCase(value) : '—'
}

/**
 * Shows a person reference (case owner, alert assignee) by display name. Falls
 * back to the raw id only when the API could not resolve a name.
 */
export function formatUserRef(name: string | null | undefined, id: string | null): string {
  if (!id) {
    return 'Unassigned'
  }

  return name ?? id
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
