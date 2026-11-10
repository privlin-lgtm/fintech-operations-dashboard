import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AlertActionsPanel } from '@/features/alerts/components/AlertActionsPanel'
import { CaseActionsPanel } from '@/features/cases/components/CaseActionsPanel'
import { useHasPermission } from '@/hooks/useHasPermission'
import type { Alert } from '@/types/alert'
import type { CaseDetail } from '@/types/case'

vi.mock('@/hooks/useHasPermission', () => ({
  useHasPermission: vi.fn(),
}))

const people = [
  { id: '11111111-1111-1111-1111-111111111111', full_name: 'Ava Analyst', role: 'analyst' },
  { id: '22222222-2222-2222-2222-222222222222', full_name: 'Priya Lead', role: 'team_lead' },
]

const caseItem: CaseDetail = {
  id: 'case-1',
  case_number: 'CASE-0001',
  customer_id: 'cust-1',
  owner_id: people[1].id,
  owner_name: 'Priya Lead',
  case_type: 'aml_review',
  status: 'in_progress',
  priority: 'high',
  sla_due_at: null,
  resolution_code: null,
  closing_summary: null,
  closed_at: null,
  created_at: '2026-11-01T00:00:00Z',
  updated_at: '2026-11-01T00:00:00Z',
  notes: [],
}

const alert: Alert = {
  id: 'alert-1',
  customer_id: 'cust-1',
  transaction_id: null,
  case_id: null,
  assignee_id: null,
  alert_type: 'velocity',
  severity: 'high',
  status: 'new',
  triggering_reason: 'Many transfers in an hour',
  dismissal_reason: null,
  resolved_at: null,
  created_at: '2026-11-01T00:00:00Z',
  updated_at: '2026-11-01T00:00:00Z',
}

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 422 ? 'Unprocessable Entity' : '',
    json: async () => body,
  } as Response
}

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe('assign and reassign pickers', () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.mocked(useHasPermission).mockReturnValue(true)
    fetchMock = vi.fn((input: string) => {
      if (input.endsWith('/users/assignable')) return Promise.resolve(jsonResponse(people))
      return Promise.reject(new Error(`unexpected request ${input}`))
    })
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('lets a case be reassigned by picking a name, leaving out the current owner', async () => {
    renderWithQueryClient(<CaseActionsPanel caseItem={caseItem} />)

    const owner = await screen.findByLabelText('New owner')
    await waitFor(() => expect(owner).toBeEnabled())

    const labels = Array.from((owner as HTMLSelectElement).options).map((option) => option.text)
    expect(labels).toEqual(['Choose a person', 'Ava Analyst (Analyst)'])
    expect(screen.queryByPlaceholderText(/uuid/i)).not.toBeInTheDocument()
  })

  it('keeps the case page up and shows a message when reassign returns a 422 array detail', async () => {
    // Regression: a 422 whose `detail` is FastAPI's array of {loc, msg} used
    // to be rendered as a React child and white-screen the case page.
    fetchMock.mockImplementation((input: string) => {
      if (input.endsWith('/users/assignable')) return Promise.resolve(jsonResponse(people))
      if (input.endsWith('/cases/case-1/reassign')) {
        return Promise.resolve(
          jsonResponse(
            { detail: [{ type: 'uuid_parsing', loc: ['body', 'owner_id'], msg: 'Input should be a valid UUID' }] },
            422,
          ),
        )
      }
      return Promise.reject(new Error(`unexpected request ${input}`))
    })

    renderWithQueryClient(<CaseActionsPanel caseItem={caseItem} />)

    const owner = await screen.findByLabelText('New owner')
    await waitFor(() => expect(owner).toBeEnabled())
    fireEvent.change(owner, { target: { value: people[0].id } })
    fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Coverage' } })
    fireEvent.click(screen.getByRole('button', { name: 'Reassign' }))

    expect(await screen.findByText('Owner id: Input should be a valid UUID')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reassign' })).toBeInTheDocument()
  })

  it('lets a new alert be assigned by picking a name', async () => {
    renderWithQueryClient(<AlertActionsPanel alert={alert} />)

    const assignee = await screen.findByLabelText('Assignee')
    await waitFor(() => expect(assignee).toBeEnabled())

    const labels = Array.from((assignee as HTMLSelectElement).options).map((option) => option.text)
    expect(labels).toEqual(['Choose a person', 'Ava Analyst (Analyst)', 'Priya Lead (Team lead)'])
  })

  it('shows why the list could not load instead of an empty picker', async () => {
    fetchMock.mockImplementation(() =>
      Promise.resolve(jsonResponse({ detail: 'Insufficient permissions' }, 403)),
    )

    renderWithQueryClient(<AlertActionsPanel alert={alert} />)

    expect(
      await screen.findByText('Could not load people: Insufficient permissions'),
    ).toBeInTheDocument()
  })
})
