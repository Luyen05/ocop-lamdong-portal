import http from '@/services/http'
import type { AdminUser, AdminUserFilters, AdminUserListResponse } from '@/types/admin-user'

export async function listAdminUsers(filters: AdminUserFilters): Promise<AdminUserListResponse> {
  const response = await http.get<AdminUserListResponse>('/admin/users', { params: filters })
  return response.data
}

export async function updateAdminUserStatus(userId: number, isActive: boolean): Promise<AdminUser> {
  const response = await http.patch<AdminUser>(`/admin/users/${userId}/status`, {
    is_active: isActive,
  })
  return response.data
}
