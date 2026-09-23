import { describe, expect, it } from 'vitest'

import {
  externalDirectionsUrl,
  formatDistance,
  formatDuration,
  formatTicketPrice,
  isLocationType,
  locationTypeStyle,
  safeExternalUrl,
  sortVietnamese,
} from '@/utils/location'

describe('location utils', () => {
  it('dinh dang khoang cach, thoi gian va gia ve', () => {
    expect(formatDistance(420.4)).toBe('420 m')
    expect(formatDistance(2605.7)).toBe('2,6 km')
    expect(formatDistance(13661)).toBe('14 km')
    expect(formatDuration(20)).toBe('1 phút')
    expect(formatDuration(1320)).toBe('22 phút')
    expect(formatDuration(5400)).toBe('1 giờ 30 phút')
    expect(formatDuration(7200)).toBe('2 giờ')
    expect(formatTicketPrice(null)).toBe('Liên hệ')
    expect(formatTicketPrice(0)).toBe('Miễn phí')
    expect(formatTicketPrice(30000)).toContain('30.000')
  })

  it('chi chap nhan loai hinh va lien ket an toan', () => {
    expect(isLocationType('tea_coffee_farm')).toBe(true)
    expect(isLocationType('casino')).toBe(false)
    expect(isLocationType('toString')).toBe(false)
    expect(locationTypeStyle('unknown').markerIcon).toBe('geo-alt-fill')
    expect(safeExternalUrl('https://example.com/a')).toBe('https://example.com/a')
    expect(safeExternalUrl('javascript:alert(1)')).toBeNull()
    expect(safeExternalUrl('not a url')).toBeNull()
    expect(safeExternalUrl(null)).toBeNull()
  })

  it('tao lien ket chi duong ngoai va sap xep tieng Viet', () => {
    expect(externalDirectionsUrl(11.879583, 108.547398)).toBe(
      'https://www.google.com/maps/dir/?api=1&destination=11.879583%2C108.547398',
    )
    expect(sortVietnamese(['Lạc Dương', 'Đà Lạt', 'Bảo Lâm'])).toEqual(['Bảo Lâm', 'Đà Lạt', 'Lạc Dương'])
  })
})
