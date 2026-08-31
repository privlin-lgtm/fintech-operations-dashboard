import { Button } from '@/components/ui/Button'

type PaginationProps = {
  onPrevious?: () => void
  onNext?: () => void
  hasPrevious: boolean
  hasNext: boolean
  summary: string
}

export function Pagination({
  onPrevious,
  onNext,
  hasPrevious,
  hasNext,
  summary,
}: PaginationProps) {
  return (
    <div className="flex flex-col gap-3 border-t border-slate-200 bg-white px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm text-slate-500">{summary}</p>
      <div className="flex items-center gap-2">
        <Button variant="secondary" size="sm" disabled={!hasPrevious} onClick={onPrevious}>
          Previous
        </Button>
        <Button variant="secondary" size="sm" disabled={!hasNext} onClick={onNext}>
          Next
        </Button>
      </div>
    </div>
  )
}
