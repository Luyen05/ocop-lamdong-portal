import type { SocialProvider, UserRole } from '@/types/auth'
import type { SubjectStatus } from '@/types/subject'

export interface AdminUserSubject {
  id: number
  name: string
  status: SubjectStatus
}

export interface AdminUser {
  id: number
  email: string
  full_name: string
  phone: string | null
  role: UserRole
  is_active: boolean
  created_at: string
  has_password: boolean
  social_providers: SocialProvider[]
  subject: AdminUserSubject | null
}

export interface AdminUserListResponse {
  items: AdminUser[]
  page: number
  page_size: number
  total: number
}

export interface AdminUserFilters {
  q?: string
  role?: UserRole
  is_active?: boolean
  page?: number
  page_size?: number
}
