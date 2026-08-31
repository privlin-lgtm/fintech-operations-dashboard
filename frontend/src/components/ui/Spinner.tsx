type SpinnerProps = {
  label?: string
}

export function Spinner({ label = 'Loading' }: SpinnerProps) {
  return (
    <div className="flex items-center gap-3 text-sm text-slate-500" role="status">
      <span className="inline-block size-5 animate-spin rounded-full border-2 border-slate-200 border-t-brand-600" />
      <span>{label}</span>
    </div>
  )
}
