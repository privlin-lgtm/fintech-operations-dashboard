export type PaginatedResponse<T> = {
  items: T[]
  next_cursor: string | null
  limit: number
}
