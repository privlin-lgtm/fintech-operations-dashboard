import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { Can } from '@/features/auth/Can'
import { useHasPermission } from '@/hooks/useHasPermission'

vi.mock('@/hooks/useHasPermission', () => ({
  useHasPermission: vi.fn(),
}))

const mockUseHasPermission = vi.mocked(useHasPermission)

describe('Can', () => {
  it('renders children when the permission is granted', () => {
    mockUseHasPermission.mockReturnValue(true)

    render(
      <Can permission="report:schedule">
        <button>Schedule report</button>
      </Can>,
    )

    expect(screen.getByRole('button', { name: 'Schedule report' })).toBeInTheDocument()
  })

  it('renders nothing by default when the permission is denied', () => {
    mockUseHasPermission.mockReturnValue(false)

    render(
      <Can permission="report:schedule">
        <button>Schedule report</button>
      </Can>,
    )

    expect(screen.queryByRole('button', { name: 'Schedule report' })).not.toBeInTheDocument()
  })

  it('renders the fallback when the permission is denied and a fallback is given', () => {
    mockUseHasPermission.mockReturnValue(false)

    render(
      <Can permission="report:schedule" fallback={<p>Ask a team lead for access.</p>}>
        <button>Schedule report</button>
      </Can>,
    )

    expect(screen.getByText('Ask a team lead for access.')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
