import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { CaseSearchForm } from '@/features/cases/components/CaseSearchForm'
import { useHasPermission } from '@/hooks/useHasPermission'

vi.mock('@/hooks/useHasPermission', () => ({
  useHasPermission: vi.fn(),
}))

const people = [
  { id: '11111111-1111-1111-1111-111111111111', full_name: 'Ava Analyst', role: 'analyst' },
  { id: '22222222-2222-2222-2222-222222222222', full_name: 'Priya Lead', role: 'team_lead' },
]

function renderForm(onSubmit = vi.fn(), url = '/cases') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[url]}>
        <CaseSearchForm onSubmit={onSubmit} />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return onSubmit
}

describe('CaseSearchForm owner filter', () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchMock = vi.fn(() =>
      Promise.resolve({ ok: true, status: 200, statusText: '', json: async () => people } as Response),
    )
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('filters by a person picked by name, not a typed id', async () => {
    vi.mocked(useHasPermission).mockReturnValue(true)
    const onSubmit = renderForm()

    const owner = await screen.findByLabelText('Owner')
    await waitFor(() => expect(owner).toBeEnabled())
    expect(Array.from((owner as HTMLSelectElement).options).map((o) => o.text)).toEqual([
      'Anyone',
      'Ava Analyst (Analyst)',
      'Priya Lead (Team lead)',
    ])
    expect(screen.queryByPlaceholderText(/uuid/i)).not.toBeInTheDocument()

    fireEvent.change(owner, { target: { value: people[1].id } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }))

    await waitFor(() => expect(onSubmit).toHaveBeenCalled())
    expect(onSubmit.mock.calls[0][0]).toMatchObject({ assignee: people[1].id })
  })

  it('shows the owner from the URL once the people list has loaded', async () => {
    vi.mocked(useHasPermission).mockReturnValue(true)
    renderForm(vi.fn(), `/cases?assignee=${people[0].id}`)

    const owner = await screen.findByLabelText('Owner')
    await waitFor(() => expect(owner).toHaveValue(people[0].id))
  })

  it('leaves the filter out for an analyst, who only sees their own cases', () => {
    vi.mocked(useHasPermission).mockReturnValue(false)
    renderForm()

    expect(screen.queryByLabelText('Owner')).not.toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
