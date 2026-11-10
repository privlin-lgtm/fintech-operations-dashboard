import type { SelectHTMLAttributes } from 'react'

import { Select } from '@/components/ui/Select'
import { useAssignableUsers } from '@/features/users/useAssignableUsers'
import { errorMessage } from '@/lib/errors'
import { formatRoleName } from '@/lib/format'

type AssigneeSelectProps = Omit<SelectHTMLAttributes<HTMLSelectElement>, 'children'> & {
  label: string
  /** Leave this person out of the list, e.g. a case's current owner. */
  excludeId?: string | null
  error?: string
  /** Label for the empty choice; also keeps the picker usable with no people loaded (e.g. "Anyone" in a filter). */
  emptyLabel?: string
}

/** Pick a person by name; the form still submits their id. */
export function AssigneeSelect({ label, excludeId, error, emptyLabel, disabled, ...props }: AssigneeSelectProps) {
  const { data, isPending, isError, error: loadError } = useAssignableUsers()

  const people = (data ?? []).filter((person) => person.id !== excludeId)
  const placeholder = isPending
    ? 'Loading people…'
    : (emptyLabel ?? (people.length === 0 ? 'No one available' : 'Choose a person'))

  const options = [
    { label: placeholder, value: '' },
    ...people.map((person) => ({
      label: `${person.full_name} (${formatRoleName(person.role)})`,
      value: person.id,
    })),
  ]

  return (
    <Select
      label={label}
      options={options}
      disabled={disabled || isPending || (!emptyLabel && people.length === 0)}
      error={error ?? (isError ? `Could not load people: ${errorMessage(loadError)}` : undefined)}
      {...props}
    />
  )
}
