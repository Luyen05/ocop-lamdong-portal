// @vitest-environment jsdom
import { AxiosError, AxiosHeaders } from 'axios'
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { defineComponent, reactive } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import MapView from '@/views/MapView.vue'
import {
  getLocationFilterOptions,
  getMapLocations,
  getNearbyLocations,
  getRoute,
} from '@/services/locations'
import type { MapFeature, NearbyLocation } from '@/types/location'

const route = reactive({ query: {} as Record<string, string> })
const router = {
  replace: vi.fn().mockResolvedValue(undefined),
}

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => router,
}))

vi.mock('@/services/locations', () => ({
  getLocationFilterOptions: vi.fn(),
  getMapLocations: vi.fn(),
  getNearbyLocations: vi.fn(),
  getRoute: vi.fn(),
}))

const LeafletMapStub = defineComponent({
  name: 'LeafletMap',
  props: ['features', 'selectedSlug', 'userPosition', 'route'],
  emits: ['select'],
  template: '<div class="map-stub" />',
})

function feature(slug: string, name: string, coordinates: [number, number]): MapFeature {
  return {
    type: 'Feature',
    geometry: { type: 'Point', coordinates },
    properties: {
      id: slug.length,
      slug,
      name,
      type: 'tea_coffee_farm',
      type_label: 'Đồi chè & cà phê',
      district: 'Đà Lạt',
      address: `${name}, Đà Lạt`,
      opening_hours: '07:00 - 17:00',
      ticket_price: null,
      rating_avg: 0,
      primary_image_url: null,
    },
  }
}

const features = [
  feature('cau-dat-farm', 'Cầu Đất Farm', [108.547398, 11.879583]),
  feature('vuon-hong-nha-tom', 'Vườn hồng Nhà Tom', [108.45894, 11.932106]),
]

const nearbyItem: NearbyLocation = {
  id: 7,
  name: 'Vườn hồng Nhà Tom',
  slug: 'vuon-hong-nha-tom',
  type: 'fruit_garden',
  type_label: 'Vườn trái cây',
  district: 'Đà Lạt',
  address: '86 Khe Sanh',
  latitude: 11.932106,
  longitude: 108.45894,
  opening_hours: null,
  ticket_price: null,
  services: [],
  description: null,
  rating_avg: 0,
  primary_image_url: null,
  distance_m: 2428.3,
}

function mockGeolocation(result: { latitude: number; longitude: number } | { code: number }) {
  const getCurrentPosition = vi.fn((success: PositionCallback, failure: PositionErrorCallback) => {
    if ('code' in result) {
      failure({ code: result.code, PERMISSION_DENIED: 1, POSITION_UNAVAILABLE: 2, TIMEOUT: 3 } as GeolocationPositionError)
    } else {
      success({ coords: result } as GeolocationPosition)
    }
  })
  Object.defineProperty(navigator, 'geolocation', { value: { getCurrentPosition }, configurable: true })
  return getCurrentPosition
}

enableAutoUnmount(afterEach)

const mountView = () =>
  mount(MapView, {
    global: {
      stubs: {
        RouterLink: { props: ['to'], template: '<a><slot /></a>' },
        LeafletMap: LeafletMapStub,
      },
    },
  })

describe('MapView', () => {
  beforeEach(() => {
    route.query = {}
    vi.clearAllMocks()
    vi.mocked(getMapLocations).mockResolvedValue({ type: 'FeatureCollection', features })
    vi.mocked(getLocationFilterOptions).mockResolvedValue({
      types: [{ value: 'tea_coffee_farm', label: 'Đồi chè & cà phê' }],
      districts: ['Đà Lạt'],
    })
  })

  it('hien thi diem tren ban do va chon diem tu danh sach', async () => {
    const wrapper = mountView()
    await flushPromises()

    const map = wrapper.getComponent(LeafletMapStub)
    expect(map.props('features')).toHaveLength(2)
    expect(wrapper.text()).toContain('2 điểm đến đang hiển thị')

    await wrapper.findAll('.location-list button')[0].trigger('click')
    expect(router.replace).toHaveBeenCalledWith({ name: 'map', query: { diem: 'cau-dat-farm' } })
    expect(map.props('selectedSlug')).toBe('cau-dat-farm')
    expect(wrapper.get('#selected-title').text()).toBe('Cầu Đất Farm')
    expect(wrapper.get('.external-directions').attributes('href')).toContain('11.879583%2C108.547398')

    map.vm.$emit('select', 'vuon-hong-nha-tom')
    await flushPromises()
    expect(wrapper.get('#selected-title').text()).toBe('Vườn hồng Nhà Tom')
  })

  it('chon san diem tu query va bo qua slug khong ton tai', async () => {
    route.query = { diem: 'vuon-hong-nha-tom' }
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.get('#selected-title').text()).toBe('Vườn hồng Nhà Tom')

    route.query = { diem: 'khong-ton-tai' }
    vi.mocked(getMapLocations).mockResolvedValueOnce({ type: 'FeatureCollection', features })
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('#selected-title').exists()).toBe(false)
  })

  it('dinh vi va liet ke diem gan nhat kem khoang cach', async () => {
    mockGeolocation({ latitude: 11.9404, longitude: 108.4383 })
    vi.mocked(getNearbyLocations).mockResolvedValue({
      origin: { latitude: 11.9404, longitude: 108.4383 },
      radius_m: 50000,
      items: [nearbyItem],
    })
    const wrapper = mountView()
    await flushPromises()

    await wrapper.get('button.btn-outline-success').trigger('click')
    await flushPromises()

    expect(getNearbyLocations).toHaveBeenCalledWith(
      { latitude: 11.9404, longitude: 108.4383 },
      { radiusKm: 50, limit: 5, type: undefined },
    )
    expect(wrapper.get('.nearby-list').text()).toContain('2,4 km')
    expect(wrapper.getComponent(LeafletMapStub).props('userPosition')).toEqual({
      latitude: 11.9404,
      longitude: 108.4383,
    })
  })

  it('bao loi khi nguoi dung tu choi quyen vi tri', async () => {
    mockGeolocation({ code: 1 })
    const wrapper = mountView()
    await flushPromises()

    await wrapper.get('button.btn-outline-success').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Bạn chưa cho phép truy cập vị trí')
    expect(getNearbyLocations).not.toHaveBeenCalled()
  })

  it('goi y tuyen duong va ve len ban do', async () => {
    mockGeolocation({ latitude: 11.9404, longitude: 108.4383 })
    vi.mocked(getNearbyLocations).mockResolvedValue({
      origin: { latitude: 11.9404, longitude: 108.4383 },
      radius_m: 50000,
      items: [],
    })
    vi.mocked(getRoute).mockResolvedValue({
      provider: 'OSRM',
      profile: 'driving',
      origin: { latitude: 11.9404, longitude: 108.4383 },
      destination: { slug: 'cau-dat-farm', name: 'Cầu Đất Farm', latitude: 11.879583, longitude: 108.547398 },
      distance_m: 15234.6,
      duration_s: 1320,
      geometry: { type: 'LineString', coordinates: [[108.4383, 11.9404], [108.547398, 11.879583]] },
    })
    route.query = { diem: 'cau-dat-farm' }
    const wrapper = mountView()
    await flushPromises()

    const routeButton = wrapper.findAll('.selected-actions button')[0]
    await routeButton.trigger('click')
    await flushPromises()

    expect(getRoute).toHaveBeenCalledWith('cau-dat-farm', { latitude: 11.9404, longitude: 108.4383 })
    expect(wrapper.get('.route-summary').text()).toContain('15 km')
    expect(wrapper.get('.route-summary').text()).toContain('22 phút')
    expect(wrapper.getComponent(LeafletMapStub).props('route')).toHaveLength(2)
  })

  it('hien thong bao than thien khi dich vu chi duong loi', async () => {
    mockGeolocation({ latitude: 11.9404, longitude: 108.4383 })
    vi.mocked(getNearbyLocations).mockResolvedValue({
      origin: { latitude: 11.9404, longitude: 108.4383 },
      radius_m: 50000,
      items: [],
    })
    vi.mocked(getRoute).mockRejectedValue(
      new AxiosError('Unavailable', 'ERR_BAD_RESPONSE', undefined, undefined, {
        status: 503,
        statusText: 'Service Unavailable',
        headers: {},
        config: { headers: new AxiosHeaders() },
        data: { code: 'ROUTING_UNAVAILABLE', message: 'Dịch vụ chỉ đường tạm thời không phản hồi.', details: null },
      }),
    )
    route.query = { diem: 'cau-dat-farm' }
    const wrapper = mountView()
    await flushPromises()

    await wrapper.findAll('.selected-actions button')[0].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Dịch vụ chỉ đường tạm thời không phản hồi.')
    expect(wrapper.find('.route-summary').exists()).toBe(false)
    expect(wrapper.find('.external-directions').exists()).toBe(true)
  })

  it('hien thi loi khi khong tai duoc du lieu ban do', async () => {
    vi.mocked(getMapLocations).mockRejectedValueOnce(new Error('network'))
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.get('.alert-danger').text()).toContain('Không thể tải dữ liệu bản đồ')
  })
})
