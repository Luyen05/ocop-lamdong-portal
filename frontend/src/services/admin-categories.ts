import http from '@/services/http'
import type {
  AdminCategory,
  AdminCategoryListResponse,
  AdminCategoryPayload,
} from '@/types/category'

export async function listAdminCategories(): Promise<AdminCategoryListResponse> {
  const response = await http.get<AdminCategoryListResponse>('/admin/categories')
  return response.data
}

export async function createAdminCategory(payload: AdminCategoryPayload): Promise<AdminCategory> {
  const response = await http.post<AdminCategory>('/admin/categories', payload)
  return response.data
}

export async function updateAdminCategory(
  categoryId: number,
  payload: Partial<AdminCategoryPayload>,
): Promise<AdminCategory> {
  const response = await http.patch<AdminCategory>(`/admin/categories/${categoryId}`, payload)
  return response.data
}

export async function deleteAdminCategory(categoryId: number): Promise<void> {
  await http.delete(`/admin/categories/${categoryId}`)
}
