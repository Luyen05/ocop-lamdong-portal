import http from '@/services/http'
import type { CategoryListResponse } from '@/types/category'

/** Danh mục đang hiển thị, theo thứ tự admin sắp (danh mục ẩn không có trong danh sách). */
export async function getCategories(): Promise<CategoryListResponse> {
  const response = await http.get<CategoryListResponse>('/categories', {
    params: { page: 1, page_size: 100, sort: 'order' },
  })
  return response.data
}
