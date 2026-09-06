import http from '@/services/http'
import type { CategoryListResponse } from '@/types/category'

export async function getCategories(): Promise<CategoryListResponse> {
  const response = await http.get<CategoryListResponse>('/categories', {
    params: { page: 1, page_size: 100, sort: 'name' },
  })
  return response.data
}
