export type ReviewStatus = 'pending' | 'approved' | 'rejected'
export type ReviewTargetType = 'product' | 'location'

export interface PublicReview {
  id: number
  rating: number
  comment: string
  author_name: string
  created_at: string
  updated_at: string
}

export interface ReviewSummary {
  average: number
  count: number
  /** Khóa "1".."5": số đánh giá đã duyệt theo từng mức sao. */
  distribution: Record<string, number>
}

export interface PublicReviewListResponse {
  items: PublicReview[]
  page: number
  page_size: number
  total: number
  summary: ReviewSummary
}

export interface ReviewTarget {
  type: ReviewTargetType
  id: number
  name: string
  slug: string
}

export interface MyReview {
  id: number
  rating: number
  comment: string
  status: ReviewStatus
  rejection_reason: string | null
  reviewed_at: string | null
  created_at: string
  updated_at: string
  target: ReviewTarget
}

export interface MyReviewListResponse {
  items: MyReview[]
  page: number
  page_size: number
  total: number
}

export interface MyReviewFilters {
  page?: number
  page_size?: number
  product_id?: number
  location_id?: number
}

export interface ReviewPayload {
  rating: number
  comment: string
}

export interface AdminReview extends MyReview {
  author: { id: number; full_name: string; email: string }
  reviewed_by_name: string | null
}

export interface AdminReviewListResponse {
  items: AdminReview[]
  page: number
  page_size: number
  total: number
}

export interface AdminReviewFilters {
  page?: number
  page_size?: number
  status?: ReviewStatus
  target?: ReviewTargetType
  q?: string
}

export interface ReviewModerationPayload {
  action: 'approve' | 'reject'
  reason?: string | null
}
