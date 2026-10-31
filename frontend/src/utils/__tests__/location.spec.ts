import { describe, expect, it } from 'vitest'

import {
  externalDirectionsUrl,
  formatDistance,
  formatDuration,
  formatTicketPrice,
  countFeaturesByType,
  hasValidCoordinates,
  isInsideLamDong,
  isLocationType,
  isSameQuery,
  matchesNearbyFilters,
  mergeQuery,
  nearbyToFeature,
  splitMappableFeatures,
  locationTypeStyle,
  safeExternalUrl,
  sortVietnamese,
} from '@/utils/location'
import type { MapFeature, NearbyLocation } from '@/types/location'

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


function pointFeature(slug: string, coordinates: unknown, type: MapFeature['properties']['type'] = 'fruit_garden'): MapFeature {
  return {
    type: 'Feature',
    geometry: { type: 'Point', coordinates } as MapFeature['geometry'],
    properties: {
      id: 1, slug, name: slug, type, type_label: type === 'fruit_garden' ? 'Vườn trái cây' : 'Khác',
      district: 'Đà Lạt', address: 'x', opening_hours: null, ticket_price: null, rating_avg: 0, primary_image_url: null,
    },
  }
}

describe('toa do ban do', () => {
  it('chi nhan toa do huu han nam trong khung Lam Dong', () => {
    expect(hasValidCoordinates(pointFeature('a', [108.45, 11.94]))).toBe(true)
    expect(hasValidCoordinates(pointFeature('a', [0, 0]))).toBe(false)
    expect(hasValidCoordinates(pointFeature('a', null))).toBe(false)
    expect(hasValidCoordinates(pointFeature('a', [null, null]))).toBe(false)
    expect(hasValidCoordinates(pointFeature('a', [Number.NaN, 11.9]))).toBe(false)
    expect(hasValidCoordinates(pointFeature('a', [108.4, Number.POSITIVE_INFINITY]))).toBe(false)
    expect(hasValidCoordinates(pointFeature('a', [105.8, 21.0]))).toBe(false) // Ha Noi
    expect(hasValidCoordinates(pointFeature('a', [11.94, 108.45]))).toBe(false) // dao thu tu
    expect(hasValidCoordinates(pointFeature('a', ['108.4', '11.9']))).toBe(false)
  })

  it('tach diem ve duoc va diem chua co toa do hop le', () => {
    const { mappable, unmappable } = splitMappableFeatures([
      pointFeature('ok', [108.45, 11.94]),
      pointFeature('null', null),
      pointFeature('zero', [0, 0]),
    ])
    expect(mappable.map((item) => item.properties.slug)).toEqual(['ok'])
    expect(unmappable.map((item) => item.properties.slug)).toEqual(['null', 'zero'])
  })

  it('xac dinh vi tri nguoi dung nam trong Lam Dong', () => {
    expect(isInsideLamDong({ latitude: 11.94, longitude: 108.45 })).toBe(true)
    expect(isInsideLamDong({ latitude: 21.03, longitude: 105.85 })).toBe(false)
  })
})

describe('chu giai loai hinh', () => {
  it('dem diem theo loai hinh co that, nhieu diem len truoc', () => {
    const entries = countFeaturesByType([
      pointFeature('a', [108.4, 11.9], 'other'),
      pointFeature('b', [108.4, 11.9], 'fruit_garden'),
      pointFeature('c', [108.4, 11.9], 'fruit_garden'),
    ])
    expect(entries).toEqual([
      { type: 'fruit_garden', label: 'Vườn trái cây', count: 2 },
      { type: 'other', label: 'Khác', count: 1 },
    ])
    expect(countFeaturesByType([])).toEqual([])
  })

  it('hai loai hinh dairy_farm va other khong dung chung mau', () => {
    expect(locationTypeStyle('dairy_farm').color).not.toBe(locationTypeStyle('other').color)
    const colors = ['tea_coffee_farm', 'fruit_garden', 'flower_garden', 'dairy_farm', 'vegetable_farm', 'craft_village', 'farmstay', 'other']
      .map((type) => locationTypeStyle(type).color)
    expect(new Set(colors).size).toBe(colors.length)
  })
})

describe('query ban do', () => {
  it('giu tham so khac khi hop nhat va xoa tham so rong', () => {
    expect(mergeQuery({ type: 'farmstay', district: 'Đà Lạt', diem: 'a' }, { diem: 'b' })).toEqual({
      type: 'farmstay', district: 'Đà Lạt', diem: 'b',
    })
    expect(mergeQuery({ type: 'farmstay', diem: 'a' }, { type: '', diem: undefined })).toEqual({})
    expect(mergeQuery({ diem: 'a', action: 'route' }, { action: undefined, search: 'dâu' })).toEqual({
      diem: 'a', search: 'dâu',
    })
    expect(mergeQuery({ x: null, y: ['1', '2'] } as never, {})).toEqual({ y: ['1', '2'] })
  })

  it('so sanh query khong phu thuoc thu tu khoa', () => {
    expect(isSameQuery({ a: '1', b: '2' }, { b: '2', a: '1' })).toBe(true)
    expect(isSameQuery({ a: '1' }, { a: '2' })).toBe(false)
    expect(isSameQuery({}, { a: '1' })).toBe(false)
  })
})

describe('diem gan ban', () => {
  const item: NearbyLocation = {
    id: 7, name: 'Vườn dâu Cầu Đất', slug: 'vuon-dau', type: 'fruit_garden', type_label: 'Vườn trái cây',
    district: 'Đà Lạt', address: '86 Khe Sanh', latitude: 11.93, longitude: 108.45, opening_hours: null,
    ticket_price: null, services: [], description: 'Hái dâu tươi', rating_avg: 0, primary_image_url: null, distance_m: 100,
  }

  it('loc theo dia ban va tu khoa nhu backend', () => {
    expect(matchesNearbyFilters(item, {})).toBe(true)
    expect(matchesNearbyFilters(item, { district: ' đà lạt ' })).toBe(true)
    expect(matchesNearbyFilters(item, { district: 'Đức Trọng' })).toBe(false)
    expect(matchesNearbyFilters(item, { search: 'DÂU' })).toBe(true)
    expect(matchesNearbyFilters(item, { search: 'khe sanh' })).toBe(true)
    expect(matchesNearbyFilters(item, { search: 'tươi' })).toBe(true)
    expect(matchesNearbyFilters(item, { search: 'chè' })).toBe(false)
    expect(matchesNearbyFilters(item, { search: 'dâu', district: 'Lạc Dương' })).toBe(false)
  })

  it('dung feature tu ket qua gan ban theo thu tu [kinh do, vi do]', () => {
    const feature = nearbyToFeature(item)
    expect(feature.geometry.coordinates).toEqual([108.45, 11.93])
    expect(feature.properties.slug).toBe('vuon-dau')
    expect(hasValidCoordinates(feature)).toBe(true)
  })
})
