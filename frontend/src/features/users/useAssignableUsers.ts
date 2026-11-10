import { useQuery } from '@tanstack/react-query'

import { fetchAssignableUsers } from '@/features/users/usersApi'
import { userKeys } from '@/lib/queryKeys'

/** People a case or alert can be handed to. Rarely changes, so cache it for a few minutes. */
export function useAssignableUsers() {
  return useQuery({
    queryKey: userKeys.assignable(),
    queryFn: fetchAssignableUsers,
    staleTime: 5 * 60 * 1000,
  })
}
