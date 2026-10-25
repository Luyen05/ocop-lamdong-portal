import http from '@/services/http'
import type {
  AdminReview,
  AdminReviewFilters,
  AdminReviewListResponse,
  MyReview,
  MyReviewFilters,
  MyReviewListResponse,
  PublicReviewListResponse,
  ReviewModerationPayload,
  ReviewPayload,
  ReviewTargetType,
} from '@/types/review'

const TARGET_PATHS: Record<ReviewTargetType, string> = {
  product: 'products',
  location: 'locations',
}

function targetPath(targetType: ReviewTargetType, targetId: number): string {
  return `/${TARGET_PATHS[targetType]}/${targetId}/reviews`
}

/** Đánh giá đã duyệt của một sản phẩm hoặc điểm du lịch, kèm tóm tắt số sao. */
export async function getPublicReviews(
  targetType: ReviewTargetType,
  targetId: number,
  params: { page?: number; page_size?: number } = {},
): Promise<PublicReviewListResponse> {
  const response = await http.get<PublicReviewListResponse>(targetPath(targetType, targetId), { params })
  return response.data
}

export async function createReview(
  targetType: ReviewTargetType,
  targetId: number,
  payload: ReviewPayload,
): Promise<MyReview> {
  const response = await http.post<MyReview>(targetPath(targetType, targetId), payload)
  return response.data
}

export async function listMyReviews(filters: MyReviewFilters = {}): Promise<MyReviewListResponse> {
  const response = await http.get<MyReviewListResponse>('/reviews/me', { params: filters })
  return response.data
}

export async function updateReview(reviewId: number, payload: Partial<ReviewPayload>): Promise<MyReview> {
  const response = await http.patch<MyReview>(`/reviews/${reviewId}`, payload)
  return response.data
}

export async function deleteReview(reviewId: number): Promise<void> {
  await http.delete(`/reviews/${reviewId}`)
}

export async function listAdminReviews(filters: AdminReviewFilters): Promise<AdminReviewListResponse> {
  const response = await http.get<AdminReviewListResponse>('/admin/reviews', { params: filters })
  return response.data
}

export async function moderateReview(
  reviewId: number,
  payload: ReviewModerationPayload,
): Promise<AdminReview> {
  const response = await http.patch<AdminReview>(`/admin/reviews/${reviewId}/moderation`, payload)
  return response.data
}
