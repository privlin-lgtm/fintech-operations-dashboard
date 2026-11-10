// Query key factories, one per domain. Hierarchical keys so a mutation can
// invalidate precisely — e.g. closing one case invalidates that case's detail
// and every case list, without touching alerts, customers, or anything else.

export const authKeys = {
  all: ['auth'] as const,
  me: () => [...authKeys.all, 'me'] as const,
}

export const customerKeys = {
  all: ['customers'] as const,
  lists: () => [...customerKeys.all, 'search'] as const,
  list: (filters: unknown) => [...customerKeys.lists(), filters] as const,
  details: () => [...customerKeys.all, 'profile'] as const,
  detail: (id: string) => [...customerKeys.details(), id] as const,
}

export const caseKeys = {
  all: ['cases'] as const,
  lists: () => [...caseKeys.all, 'search'] as const,
  list: (filters: unknown) => [...caseKeys.lists(), filters] as const,
  details: () => [...caseKeys.all, 'detail'] as const,
  detail: (id: string) => [...caseKeys.details(), id] as const,
}

export const alertKeys = {
  all: ['alerts'] as const,
  lists: () => [...alertKeys.all, 'search'] as const,
  list: (filters: unknown) => [...alertKeys.lists(), filters] as const,
  details: () => [...alertKeys.all, 'detail'] as const,
  detail: (id: string) => [...alertKeys.details(), id] as const,
}

export const transactionKeys = {
  all: ['transactions'] as const,
  lists: () => [...transactionKeys.all, 'search'] as const,
  list: (filters: unknown) => [...transactionKeys.lists(), filters] as const,
  details: () => [...transactionKeys.all, 'detail'] as const,
  detail: (id: string) => [...transactionKeys.details(), id] as const,
}

export const reportKeys = {
  all: ['reports'] as const,
  detail: (reportType: string, filters: unknown) => [...reportKeys.all, reportType, filters] as const,
}

export const dashboardKeys = {
  all: ['dashboard'] as const,
  summary: () => [...dashboardKeys.all, 'summary'] as const,
}

export const userKeys = {
  all: ['users'] as const,
  assignable: () => [...userKeys.all, 'assignable'] as const,
}
