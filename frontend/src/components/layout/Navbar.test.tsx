import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { Navbar } from '@/components/layout/Navbar'
import { useAuth } from '@/features/auth/AuthProvider'

vi.mock('@/features/auth/AuthProvider', () => ({
  useAuth: vi.fn(),
}))

const mockUseAuth = vi.mocked(useAuth)

describe('Navbar', () => {
  it('shows the role label in sentence case', () => {
    mockUseAuth.mockReturnValue({
      user: { full_name: 'Priya Shah', email: 'priya@example.com', role: { name: 'team_lead' } },
      logout: vi.fn(),
    } as unknown as ReturnType<typeof useAuth>)

    render(<Navbar />)

    expect(screen.getByText('Team lead')).toBeInTheDocument()
    expect(screen.queryByText('team_lead')).not.toBeInTheDocument()
  })
})
