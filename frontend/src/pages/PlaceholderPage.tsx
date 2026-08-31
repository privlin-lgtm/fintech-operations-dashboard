import { Card } from '@/components/ui/Card'

type PlaceholderPageProps = {
  title: string
  description: string
}

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        <p className="mt-1 text-sm text-slate-500">{description}</p>
      </div>
      <Card title="Coming soon">
        <p className="text-sm text-slate-600">
          This module route is part of the frontend scaffold. Connect it to the corresponding
          FastAPI endpoints when you are ready.
        </p>
      </Card>
    </div>
  )
}
