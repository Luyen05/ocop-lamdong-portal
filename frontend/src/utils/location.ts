import type { Coordinate, LocationType, MapFeature, NearbyLocation } from '@/types/location'

interface LocationTypeStyle {
  /** Tên icon cho AppIcon. */
  icon: string
  /** Tên Bootstrap Icons dùng trực tiếp trong marker Leaflet. */
  markerIcon: string
  color: string
  illustration: string
}

const defaultStyle: LocationTypeStyle = {
  icon: 'map-pin',
  markerIcon: 'geo-alt-fill',
  // Khác với màu nhóm "Trang trại bò sữa" (sky) vốn gần màu --ocop-location-other: dùng sắc trung tính tối.
  color: 'var(--ocop-neutral-900)',
  illustration: '/assets/images/tourism-farm.svg',
}

const typeStyles: Record<LocationType, LocationTypeStyle> = {
  tea_coffee_farm: { icon: 'coffee', markerIcon: 'cup-hot-fill', color: 'var(--ocop-location-tea-coffee)', illustration: '/assets/images/tourism-tea.svg' },
  fruit_garden: { icon: 'sprout', markerIcon: 'basket-fill', color: 'var(--ocop-location-fruit)', illustration: '/assets/images/tourism-strawberry.svg' },
  flower_garden: { icon: 'flower', markerIcon: 'flower1', color: 'var(--ocop-location-flower)', illustration: '/assets/images/tourism-farm.svg' },
  dairy_farm: { icon: 'building', markerIcon: 'house-heart-fill', color: 'var(--ocop-location-dairy)', illustration: '/assets/images/tourism-farm.svg' },
  vegetable_farm: { icon: 'wheat', markerIcon: 'flower3', color: 'var(--ocop-location-vegetable)', illustration: '/assets/images/tourism-farm.svg' },
  craft_village: { icon: 'palette', markerIcon: 'palette-fill', color: 'var(--ocop-location-craft)', illustration: '/assets/images/tourism-farm.svg' },
  farmstay: { icon: 'home', markerIcon: 'house-fill', color: 'var(--ocop-location-farmstay)', illustration: '/assets/images/tourism-farm.svg' },
  other: defaultStyle,
}

export function isLocationType(value: unknown): value is LocationType {
  return typeof value === 'string' && Object.prototype.hasOwnProperty.call(typeStyles, value)
}

export function locationTypeStyle(type: string): LocationTypeStyle {
  return typeStyles[type as LocationType] ?? defaultStyle
}

export function formatTicketPrice(price: number | null): string {
  if (price === null) return 'Liên hệ'
  if (price <= 0) return 'Miễn phí'
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(price)
}

export function formatDistance(meters: number): string {
  if (meters < 1000) return `${Math.round(meters)} m`
  const kilometers = meters / 1000
  return `${kilometers.toLocaleString('vi-VN', { maximumFractionDigits: kilometers < 10 ? 1 : 0 })} km`
}

export function formatDuration(seconds: number): string {
  const totalMinutes = Math.max(1, Math.round(seconds / 60))
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  if (!hours) return `${totalMinutes} phút`
  return minutes ? `${hours} giờ ${minutes} phút` : `${hours} giờ`
}

/** Liên kết mở chỉ đường bằng ứng dụng bản đồ bên ngoài, dùng khi OSRM không phản hồi. */
export function externalDirectionsUrl(latitude: number, longitude: number): string {
  const destination = `${latitude.toFixed(6)},${longitude.toFixed(6)}`
  return `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(destination)}`
}

export function sortVietnamese(values: string[]): string[] {
  return [...values].sort((first, second) => first.localeCompare(second, 'vi'))
}

/** Chỉ cho phép liên kết http/https để tránh chèn javascript: từ dữ liệu người dùng. */
export function safeExternalUrl(value: string | null | undefined): string | null {
  if (!value) return null
  try {
    const url = new URL(value)
    return url.protocol === 'http:' || url.protocol === 'https:' ? url.toString() : null
  } catch {
    return null
  }
}

/** Khung bao Lâm Đồng (dự phòng): tọa độ nằm ngoài khung này bị coi là sai dữ liệu khi vẽ bản đồ. */
export const LAM_DONG_BOUNDS = { minLat: 10.2, maxLat: 12.6, minLng: 106.6, maxLng: 109.0 } as const

export function isValidMapCoordinate(latitude: unknown, longitude: unknown): boolean {
  return (
    typeof latitude === 'number' &&
    typeof longitude === 'number' &&
    Number.isFinite(latitude) &&
    Number.isFinite(longitude) &&
    latitude >= LAM_DONG_BOUNDS.minLat &&
    latitude <= LAM_DONG_BOUNDS.maxLat &&
    longitude >= LAM_DONG_BOUNDS.minLng &&
    longitude <= LAM_DONG_BOUNDS.maxLng
  )
}

/** Điểm có tọa độ GeoJSON [kinh độ, vĩ độ] hợp lệ để vẽ marker và fitBounds. */
export function hasValidCoordinates(feature: MapFeature): boolean {
  const coordinates = feature?.geometry?.coordinates as unknown
  if (!Array.isArray(coordinates)) return false
  return isValidMapCoordinate(coordinates[1], coordinates[0])
}

export function splitMappableFeatures(features: MapFeature[]): {
  mappable: MapFeature[]
  unmappable: MapFeature[]
} {
  const mappable: MapFeature[] = []
  const unmappable: MapFeature[] = []
  for (const feature of features) (hasValidCoordinates(feature) ? mappable : unmappable).push(feature)
  return { mappable, unmappable }
}

export function isInsideLamDong(position: Coordinate): boolean {
  return isValidMapCoordinate(position.latitude, position.longitude)
}

export interface LegendEntry {
  type: LocationType
  label: string
  count: number
}

/** Các loại hình có thật trong dữ liệu kèm số điểm, nhiều điểm nhất lên trước. */
export function countFeaturesByType(features: MapFeature[]): LegendEntry[] {
  const entries = new Map<LocationType, LegendEntry>()
  for (const feature of features) {
    const { type, type_label: label } = feature.properties
    const entry = entries.get(type)
    if (entry) entry.count += 1
    else entries.set(type, { type, label, count: 1 })
  }
  return [...entries.values()].sort(
    (first, second) => second.count - first.count || first.label.localeCompare(second.label, 'vi'),
  )
}

/**
 * Hợp nhất query hiện tại với thay đổi: giữ các tham số khác (vd. diem), giá trị rỗng/undefined
 * trong patch nghĩa là xóa tham số đó.
 */
export function mergeQuery(
  current: Record<string, unknown>,
  patch: Record<string, string | undefined | null>,
): Record<string, string | string[]> {
  const merged: Record<string, string | string[]> = {}
  for (const [key, value] of Object.entries(current)) {
    if (typeof value === 'string') merged[key] = value
    else if (Array.isArray(value)) {
      const items = value.filter((item): item is string => typeof item === 'string')
      if (items.length) merged[key] = items
    }
  }
  for (const [key, value] of Object.entries(patch)) {
    if (value === undefined || value === null || value === '') delete merged[key]
    else merged[key] = value
  }
  return merged
}

export function isSameQuery(first: Record<string, unknown>, second: Record<string, unknown>): boolean {
  const normalize = (query: Record<string, unknown>) =>
    JSON.stringify(Object.entries(mergeQuery(query, {})).sort(([a], [b]) => a.localeCompare(b)))
  return normalize(first) === normalize(second)
}

/** Chuẩn hóa để so khớp không phân biệt hoa thường và khoảng trắng đầu/cuối (khớp cách backend lọc). */
function normalizeText(value: string | null | undefined): string {
  return (value ?? '').trim().toLowerCase()
}

/**
 * API /map/nearby chỉ lọc theo loại hình; địa bàn và từ khóa được lọc phía client trên kết quả trả về
 * theo cùng quy tắc với /map/locations (địa bàn khớp nguyên; từ khóa nằm trong tên, mô tả hoặc địa chỉ).
 */
export function matchesNearbyFilters(
  item: Pick<NearbyLocation, 'name' | 'district' | 'address' | 'description'>,
  filters: { search?: string; district?: string },
): boolean {
  const district = normalizeText(filters.district)
  if (district && normalizeText(item.district) !== district) return false
  const keyword = normalizeText(filters.search)
  if (!keyword) return true
  return [item.name, item.description, item.address].some((text) => normalizeText(text).includes(keyword))
}

/** Dựng feature bản đồ từ kết quả "điểm gần bạn" để vẫn hiển thị được điểm nằm ngoài bộ lọc hiện tại. */
export function nearbyToFeature(item: NearbyLocation): MapFeature {
  return {
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [item.longitude, item.latitude] },
    properties: {
      id: item.id,
      slug: item.slug,
      name: item.name,
      type: item.type,
      type_label: item.type_label,
      district: item.district,
      address: item.address,
      opening_hours: item.opening_hours,
      ticket_price: item.ticket_price,
      rating_avg: item.rating_avg,
      primary_image_url: item.primary_image_url,
    },
  }
}
