import type {
  LocationChangeRequest,
  LocationSource,
  LocationWorkflowStatus,
  ManagedLocation,
} from '@/types/location-management'
import { formatDistance } from '@/utils/location'

export type StatusTone = 'neutral' | 'info' | 'warning' | 'success' | 'accent' | 'danger'

interface StatusMeta {
  label: string
  tone: StatusTone
  /** Giải thích cho chủ thể ở phần chú thích trạng thái. */
  hint: string
}

export const LOCATION_STATUS_META: Record<LocationWorkflowStatus, StatusMeta> = {
  draft: { label: 'Bản nháp', tone: 'neutral', hint: 'Chỉ bạn thấy. Sửa tự do, gửi duyệt khi đủ thông tin.' },
  pending: { label: 'Chờ duyệt', tone: 'info', hint: 'Quản trị viên đang kiểm tra. Không sửa được trong lúc chờ.' },
  needs_revision: { label: 'Cần bổ sung', tone: 'warning', hint: 'Xem ghi chú của quản trị viên, sửa rồi gửi lại.' },
  approved: { label: 'Đã duyệt', tone: 'success', hint: 'Đang hiện trên bản đồ. Muốn sửa thì gửi yêu cầu cập nhật.' },
  rejected: { label: 'Bị từ chối', tone: 'danger', hint: 'Có lý do kèm theo. Có thể khai báo lại thành điểm mới.' },
  archived: { label: 'Ngừng hiển thị', tone: 'neutral', hint: 'Đã gỡ khỏi bản đồ theo đề nghị của đơn vị.' },
}

export const LOCATION_SOURCE_LABELS: Record<LocationSource, string> = {
  admin_import: 'Nhóm nhập từ nguồn công khai',
  map_pin: 'Ghim trên bản đồ',
  device_gps: 'GPS của thiết bị',
  coordinates: 'Tọa độ dán vào',
  google_maps_link: 'Link Google Maps',
}

/** Loại hình theo thứ tự hiển thị trong ô chọn (khớp LOCATION_TYPES ở backend). */
export const LOCATION_TYPE_OPTIONS = [
  { value: 'fruit_garden', label: 'Vườn trái cây' },
  { value: 'tea_coffee_farm', label: 'Đồi chè & cà phê' },
  { value: 'flower_garden', label: 'Vườn hoa' },
  { value: 'dairy_farm', label: 'Nông trại chăn nuôi' },
  { value: 'vegetable_farm', label: 'Nông trại rau & nấm' },
  { value: 'craft_village', label: 'Làng nghề' },
  { value: 'farmstay', label: 'Farmstay & nghỉ dưỡng' },
  { value: 'other', label: 'Loại hình khác' },
] as const

/** Gợi ý dịch vụ; chủ thể có thể thêm dịch vụ khác. */
export const SERVICE_SUGGESTIONS = [
  'Tham quan vườn',
  'Tự tay thu hoạch',
  'Chụp ảnh',
  'Mua sản phẩm tại chỗ',
  'Ăn uống',
  'Lưu trú',
]

export const MIN_LOCATION_DESCRIPTION = 40

export function activeChangeRequest(
  location: ManagedLocation,
  requests: LocationChangeRequest[],
): LocationChangeRequest | undefined {
  return requests.find(
    (request) => request.location_id === location.id && ['pending', 'needs_revision'].includes(request.status),
  )
}

export function formatAccuracy(meters: number | null | undefined): string {
  if (meters === null || meters === undefined) return 'Không có (chỉ có khi dùng GPS)'
  const rounded = Math.round(meters)
  const quality = rounded <= 20 ? 'tốt' : rounded <= 50 ? 'khá' : 'thấp, nên kéo ghim về đúng chỗ'
  return `± ${rounded} m (${quality})`
}

export function formatCoordinate(latitude: number | null, longitude: number | null): string {
  if (latitude === null || longitude === null) return 'Chưa có'
  return `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`
}

export function nearestLabel(distance: number): string {
  return `khoảng ${formatDistance(distance)}`
}

export function formatDate(value: string | null): string {
  return value ? new Intl.DateTimeFormat('vi-VN').format(new Date(value)) : '—'
}

export function formatDateTime(value: string | null): string {
  return value
    ? new Intl.DateTimeFormat('vi-VN', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value))
    : '—'
}

export function googleMapsUrl(latitude: number, longitude: number): string {
  return `https://www.google.com/maps/search/?api=1&query=${latitude.toFixed(6)},${longitude.toFixed(6)}`
}

/**
 * Khung tọa độ tỉnh Lâm Đồng (gồm Đắk Nông, Bình Thuận cũ), trùng với LAM_DONG_BOUNDS ở backend
 * (services/location_workflow.py). Dùng để báo ngay trên form; backend vẫn kiểm tra lại khi gửi duyệt.
 */
export const LAM_DONG_BOUNDS = { minLatitude: 10.4, maxLatitude: 12.9, minLongitude: 107.1, maxLongitude: 109.0 }

export function insideLamDong(latitude: number, longitude: number): boolean {
  return (
    latitude >= LAM_DONG_BOUNDS.minLatitude &&
    latitude <= LAM_DONG_BOUNDS.maxLatitude &&
    longitude >= LAM_DONG_BOUNDS.minLongitude &&
    longitude <= LAM_DONG_BOUNDS.maxLongitude
  )
}
