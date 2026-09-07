export type SubjectType = 'cooperative' | 'enterprise' | 'household' | 'individual'
export type SubjectStatus = 'pending' | 'approved' | 'rejected'

export interface SubjectApplicationPayload {
  name: string
  type: SubjectType
  tax_code: string | null
  representative: string
  phone: string
  email: string | null
  address: string
  district: string
}

export interface SubjectApplication extends SubjectApplicationPayload {
  id: number
  user_id: number
  status: SubjectStatus
  moderation_note: string | null
  created_at: string
  updated_at: string
}

export interface SubjectApplicant {
  id: number
  email: string
  full_name: string
  role: 'admin' | 'subject' | 'user'
  is_active: boolean
}

export interface AdminSubjectApplication extends SubjectApplication {
  applicant: SubjectApplicant
}

export interface SubjectApplicationListResponse {
  items: AdminSubjectApplication[]
  page: number
  page_size: number
  total: number
}

export interface SubjectApplicationFilters {
  page?: number
  page_size?: number
  search?: string
  status?: SubjectStatus
}

export interface SubjectModerationPayload {
  status: 'approved' | 'rejected'
  note?: string | null
}
