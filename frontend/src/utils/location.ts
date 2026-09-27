import type { LocationType } from '@/types/location'

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
  color: 'var(--ocop-location-other)',
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
