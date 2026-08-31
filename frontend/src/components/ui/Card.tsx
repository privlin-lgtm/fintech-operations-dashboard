import type { ReactNode } from 'react'

type CardProps = {
  title?: string
  description?: string
  children: ReactNode
  className?: string
}

export function Card({ title, description, children, className = '' }: CardProps) {
  return (
    <section
      className={`rounded-xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}
    >
      {title ? (
        <header className="mb-4">
          <h2 className="text-base font-semibold text-slate-900">{title}</h2>
          {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
        </header>
      ) : null}
      {children}
    </section>
  )
}
