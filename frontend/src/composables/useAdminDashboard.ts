import { getAdminDashboard, type AdminDashboardStats } from '@/services/admin'

let inflight: Promise<AdminDashboardStats> | null = null

/**
 * Gọi GET /admin/dashboard nhưng gộp các lượt gọi đồng thời (khung quản trị cho chuông thông báo
 * và trang Tổng quan cùng mở một lúc) thành một request.
 */
export function loadAdminDashboard(): Promise<AdminDashboardStats> {
  if (!inflight) {
    inflight = getAdminDashboard().finally(() => {
      inflight = null
    })
  }
  return inflight
}
