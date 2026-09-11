import http from '@/services/http'

export interface AdminDashboardStats {
  total_products: number
  approved_products: number
  pending_products: number
  pending_subject_applications: number
  pending_change_requests: number
  products_missing_decision: number
}

export async function getAdminDashboard(): Promise<AdminDashboardStats> {
  const response = await http.get<AdminDashboardStats>('/admin/dashboard')
  return response.data
}
