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

export interface KeyCount {
  key: string
  count: number
}

export interface AdminStatistics {
  generated_at: string
  products_by_status: KeyCount[]
  approved_by_star: { star: number; count: number }[]
  approved_by_category: { id: number; name: string; slug: string; count: number }[]
  approved_by_district: { district: string; count: number }[]
  /** Chuỗi tháng liên tục (YYYY-MM, giờ Việt Nam), kể cả tháng bằng 0. */
  approved_by_month: { month: string; count: number }[]
  approved_without_review_date: number
  certificates: {
    expired: number
    expiring_soon: number
    expiring_window_days: number
    by_year: { year: number; count: number }[]
  }
  top_viewed_products: { id: number; name: string; slug: string; views: number }[]
  subjects_by_status: KeyCount[]
  locations_by_type: KeyCount[]
}

export async function getAdminStatistics(): Promise<AdminStatistics> {
  const response = await http.get<AdminStatistics>('/admin/statistics')
  return response.data
}
