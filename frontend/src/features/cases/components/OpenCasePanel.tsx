import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Select } from '@/components/ui/Select'
import { Can } from '@/features/auth/Can'
import { useCreateCase } from '@/features/cases/hooks/useCaseSearch'
import type { ApiError } from '@/lib/api'
import { CASE_PRIORITY_OPTIONS, CASE_TYPE_OPTIONS } from '@/types/case'
import type { CasePriority, CaseType } from '@/types/case'

type OpenCaseValues = {
  caseType: CaseType
  priority: CasePriority
}

function errorMessage(error: unknown): string | null {
  if (!error) return null
  const apiError = error as ApiError
  return apiError.detail ?? apiError.message ?? 'Something went wrong.'
}

export function OpenCasePanel({ customerId }: { customerId: string }) {
  const navigate = useNavigate()
  const mutation = useCreateCase()
  const { register, handleSubmit } = useForm<OpenCaseValues>({
    defaultValues: { caseType: 'fraud', priority: 'high' },
  })

  const onSubmit = handleSubmit((values) => {
    mutation.mutate(
      {
        customer_id: customerId,
        case_type: values.caseType,
        priority: values.priority,
      },
      {
        onSuccess: (caseItem) => {
          void navigate(`/cases/${caseItem.id}`)
        },
      },
    )
  })

  return (
    <Can permission="case:create">
      <Card title="Open investigation case" description="Start a new case for this customer.">
        <form
          data-testid="open-case-form"
          onSubmit={(event) => void onSubmit(event)}
          className="space-y-3"
        >
          <Select label="Case type" options={CASE_TYPE_OPTIONS} {...register('caseType')} />
          <Select label="Priority" options={CASE_PRIORITY_OPTIONS} {...register('priority')} />
          {mutation.isError ? (
            <p className="text-sm text-red-600">{errorMessage(mutation.error)}</p>
          ) : null}
          <Button type="submit" size="sm" isLoading={mutation.isPending}>
            Open case
          </Button>
        </form>
      </Card>
    </Can>
  )
}
