// One place that turns anything a failed request can throw into a sentence a
// form can show. Every form uses errorMessage(); nothing renders `detail`
// directly, so an unexpected error shape can't white-screen a page.

const FALLBACK_MESSAGE = 'Something went wrong.'

type ValidationIssue = { loc?: unknown; msg?: unknown }

function fieldName(loc: unknown): string | null {
  if (!Array.isArray(loc)) return null
  // loc looks like ["body", "owner_id"]; the request-part prefix means nothing to a user.
  const parts = loc.filter((part) => !['body', 'query', 'path', 'header'].includes(String(part)))
  const last = parts.at(-1)
  if (last === undefined || typeof last === 'number') return null
  const spaced = String(last).replace(/_/g, ' ').trim()
  return spaced ? spaced.charAt(0).toUpperCase() + spaced.slice(1) : null
}

function describeIssue(issue: unknown): string | null {
  if (typeof issue === 'string') return issue.trim() || null
  if (issue && typeof issue === 'object') {
    const { loc, msg } = issue as ValidationIssue
    if (typeof msg === 'string' && msg.trim()) {
      const field = fieldName(loc)
      return field ? `${field}: ${msg}` : msg
    }
  }
  return null
}

/**
 * Flattens an API error body's `detail` into one string: our handlers send a
 * string, FastAPI's request validation sends a list of {loc, msg} issues.
 * Returns undefined when nothing readable is in there.
 */
export function describeErrorDetail(detail: unknown): string | undefined {
  if (typeof detail === 'string') return detail.trim() || undefined
  const issues = Array.isArray(detail) ? detail : [detail]
  const messages = issues.map(describeIssue).filter((message): message is string => Boolean(message))
  return messages.length ? messages.join('; ') : undefined
}

/** A readable message for any thrown value, or null when there is no error. Always a string otherwise. */
export function errorMessage(error: unknown): string | null {
  if (error === null || error === undefined || error === false) return null
  if (typeof error === 'string') return error.trim() || FALLBACK_MESSAGE
  if (typeof error === 'object') {
    const { detail, message } = error as { detail?: unknown; message?: unknown }
    return describeErrorDetail(detail) ?? describeErrorDetail(message) ?? FALLBACK_MESSAGE
  }
  return FALLBACK_MESSAGE
}
