import type { ReviewStatus, ReviewTarget } from '@/types/review'

/** Giống backend (app/schemas/review.py): nội dung 10–1000 ký tự sau khi bỏ khoảng trắng hai đầu. */
export const REVIEW_COMMENT_MIN = 10
export const REVIEW_COMMENT_MAX = 1000

/** Nhãn từng mức sao, dùng cho nhóm chọn sao và mô tả cho trình đọc màn hình. */
export const RATING_LABELS: Record<number, string> = {
  1: 'Rất không hài lòng',
  2: 'Chưa hài lòng',
  3: 'Tạm được',
  4: 'Hài lòng',
  5: 'Rất hài lòng',
}

export const REVIEW_STATUS_LABELS: Record<ReviewStatus, string> = {
  pending: 'Đang chờ duyệt',
  approved: 'Đang hiển thị',
  rejected: 'Bị từ chối',
}

export function validateReviewComment(comment: string): string {
  const length = comment.trim().length
  if (length < REVIEW_COMMENT_MIN) {
    return `Nhận xét cần ít nhất ${REVIEW_COMMENT_MIN} ký tự.`
  }
  if (length > REVIEW_COMMENT_MAX) {
    return `Nhận xét tối đa ${REVIEW_COMMENT_MAX} ký tự.`
  }
  return ''
}

export function formatReviewDate(value: string): string {
  return new Intl.DateTimeFormat('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(
    new Date(value),
  )
}

/** Điểm trung bình kiểu Việt Nam: 4,3 (một chữ số thập phân). */
export function formatAverage(value: number): string {
  return new Intl.NumberFormat('vi-VN', { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(value)
}

export function reviewTargetLink(target: ReviewTarget): string {
  return target.type === 'product' ? `/san-pham/${target.slug}` : `/diem-du-lich/${target.slug}`
}

export function reviewTargetTypeLabel(target: Pick<ReviewTarget, 'type'>): string {
  return target.type === 'product' ? 'Sản phẩm OCOP' : 'Điểm du lịch'
}
