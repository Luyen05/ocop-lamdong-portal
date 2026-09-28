import type { LocationType } from '@/types/location'

/** Trạng thái điểm du lịch trong quy trình khai báo – kiểm duyệt (backend: location_management.py). */
export type LocationWorkflowStatus =
  | 'draft'
  | 'pending'
  | 'needs_revision'
  | 'approved'
  | 'rejected'
  | 'archived'

/** Cách chủ thể lấy vị trí; admin_import là dữ liệu nhóm nhập từ nguồn công khai. */
export type SubjectLocationSource = 'map_pin' | 'device_gps' | 'coordinates' | 'google_maps_link'
export type LocationSource = 'admin_import' | SubjectLocationSource

export type LocationModerationStatus = 'approved' | 'needs_revision' | 'rejected'
export type LocationChangeStatus = 'pending' | 'needs_revision' | 'approved' | 'rejected' | 'cancelled'
export type LocationChangeType = 'update' | 'delete'

export interface LocationImagePayload {
  image_url: string
  storage_path: string | null
  is_primary: boolean
  sort_order: number
  alt_text?: string | null
}

/** Dữ liệu gửi khi lưu nháp; chỉ trường có mặt mới được cập nhật. */
export interface LocationDraftPayload {
  name?: string
  type?: LocationType
  description?: string | null
  latitude?: number | null
  longitude?: number | null
  location_source?: SubjectLocationSource | null
  location_accuracy_m?: number | null
  district?: string | null
  address?: string | null
  contact_phone?: string | null
  opening_hours?: string | null
  ticket_price?: number | null
  services?: string[]
  website?: string | null
  images?: LocationImagePayload[]
  product_ids?: number[]
}

/** Thông tin đầy đủ, dùng cho yêu cầu cập nhật điểm đã duyệt. */
export interface LocationWritePayload {
  name: string
  type: LocationType
  description: string
  latitude: number
  longitude: number
  location_source: SubjectLocationSource
  location_accuracy_m: number | null
  district: string
  address: string
  contact_phone: string | null
  opening_hours: string | null
  ticket_price: number | null
  services: string[]
  website: string | null
  images: LocationImagePayload[]
  product_ids: number[]
}

export interface NearestApprovedLocation {
  id: number
  name: string
  slug: string
  distance_m: number
}

export interface LocationPositionCheck {
  latitude: number
  longitude: number
  inside_lam_dong: boolean
  nearest: NearestApprovedLocation | null
  duplicate_warning: boolean
  duplicate_radius_m: number
}

export interface ManagedLocationImage extends LocationImagePayload {
  id: number
}

export interface LocationProduct {
  id: number
  name: string
  slug: string
  status: string
}

export interface LocationOwner {
  id: number
  name: string
  representative: string
  phone: string
  status: 'pending' | 'approved' | 'rejected'
  is_active: boolean
}

export interface ManagedLocation {
  id: number
  subject_id: number | null
  name: string
  slug: string
  type: LocationType
  type_label: string
  description: string | null
  latitude: number | null
  longitude: number | null
  location_source: LocationSource | null
  location_accuracy_m: number | null
  district: string | null
  address: string | null
  contact_phone: string | null
  opening_hours: string | null
  /** Backend trả số thập phân dạng chuỗi (Decimal). */
  ticket_price: string | number | null
  services: string[]
  website: string | null
  status: LocationWorkflowStatus
  submitted_at: string | null
  reviewed_at: string | null
  reviewed_by_name: string | null
  review_note: string | null
  version: number
  images: ManagedLocationImage[]
  products: LocationProduct[]
  subject: LocationOwner | null
  open_change_request_id: number | null
  position_check: LocationPositionCheck | null
  created_at: string
  updated_at: string
}

export interface ManagedLocationListResponse {
  items: ManagedLocation[]
  page: number
  page_size: number
  total: number
  status_counts: Partial<Record<LocationWorkflowStatus, number>>
}

export interface LocationImageUpload {
  image_url: string
  storage_path: string
  content_type: string
  size_bytes: number
}

export interface CoordinateParseResult {
  latitude: number
  longitude: number
  location_source: 'coordinates' | 'google_maps_link'
  position_check: LocationPositionCheck
}

export interface LocationModerationPayload {
  status: LocationModerationStatus
  note: string | null
  latitude?: number
  longitude?: number
}

export interface LocationSnapshot {
  name: string
  type: string
  description: string | null
  latitude: number | null
  longitude: number | null
  location_source: LocationSource | null
  location_accuracy_m: number | null
  district: string | null
  address: string | null
  contact_phone: string | null
  opening_hours: string | null
  ticket_price: string | number | null
  services: string[]
  website: string | null
  images: LocationImagePayload[]
  product_ids: number[]
}

export interface LocationChangeRequest {
  id: number
  location_id: number
  subject_id: number
  request_type: LocationChangeType
  current_data: LocationSnapshot
  proposed_data: (Partial<LocationWritePayload> & Record<string, unknown>) | null
  reason: string | null
  status: LocationChangeStatus
  base_version: number
  submitted_at: string
  reviewed_at: string | null
  reviewed_by_name: string | null
  review_note: string | null
  location_name: string
  location_slug: string
  subject_name: string
  proposed_position_check: LocationPositionCheck | null
  created_at: string
  updated_at: string
}

export interface LocationChangeRequestListResponse {
  items: LocationChangeRequest[]
  page: number
  page_size: number
  total: number
}

export interface AdminLocationFilters {
  status?: LocationWorkflowStatus
  origin?: 'subject' | 'import'
  search?: string
  page?: number
  page_size?: number
}
