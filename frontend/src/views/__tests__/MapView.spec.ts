// @vitest-environment jsdom
import { AxiosError, AxiosHeaders } from 'axios'
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { defineComponent, reactive } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import MapView from '@/views/MapView.vue'
import { getCategories } from '@/services/categories'
import {
  getLocationFilterOptions,
  getMapLocations,
  getNearbyLocations,
  getProductLocations,
  getPublicSubject,
  getRoute,
  getTour,
  getTours,
} from '@/services/locations'
import type { MapFeature, NearbyLocation } from '@/types/location'

const route = reactive({ query: {} as Record<string, string> })
const router = {
  replace: vi.fn().mockResolvedValue(undefined),
  push: vi.fn().mockResolvedValue(undefined),
}

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => router,
}))

vi.mock('@/services/locations', () => ({
  getLocationFilterOptions: vi.fn(),
  getMapLocations: vi.fn(),
  getNearbyLocations: vi.fn(),
  getProductLocations: vi.fn(),
  getPublicSubject: vi.fn(),
  getRoute: vi.fn(),
  getTour: vi.fn(),
  getTours: vi.fn(),
}))

vi.mock('@/services/categories', () => ({
  getCategories: vi.fn(),
}))

const LeafletMapStub = defineComponent({
  name: 'LeafletMap',
  props: ['features', 'selectedSlug', 'userPosition', 'route', 'links'],
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
      subject: { id: 1, name: 'HTX Chè Cầu Đất', district: 'Đà Lạt' },
      products: [{ id: 10, name: 'Trà xanh Cầu Đất', slug: 'tra-xanh-cau-dat', star: 4, primary_image_url: null }],
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

function shopFeature(slug: string, name: string, coordinates: [number, number], role: 'produced_here' | 'sold_here'): MapFeature {
  const base = feature(slug, name, coordinates)
  return {
    ...base,
    properties: {
      ...base.properties,
      type: 'ocop_store',
      type_label: 'Cửa hàng OCOP',
      kind: 'shop',
      contact_phone: '0263 379 8888',
      website: 'https://example.com/',
      products: [
        { id: 10, name: 'Dâu tây sấy dẻo', slug: 'dau-tay-say-deo', star: 3, primary_image_url: null, role },
      ],
    },
  }
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
    vi.mocked(getTours).mockResolvedValue([])
    vi.mocked(getCategories).mockResolvedValue({
      items: [{ id: 1, name: 'Đồ uống', slug: 'do-uong', description: null, icon: null }],
      page: 1,
      page_size: 100,
      total: 1,
    })
  })

  it('hien thi diem tren ban do va chon diem tu danh sach', async () => {
    const wrapper = mountView()
    await flushPromises()

    const map = wrapper.getComponent(LeafletMapStub)
    expect(map.props('features')).toHaveLength(2)
    expect(wrapper.text()).toContain('2 địa điểm đang hiển thị')

    await wrapper.findAll('.location-list button')[0].trigger('click')
    expect(router.replace).toHaveBeenCalledWith({ name: 'map', query: { diem: 'cau-dat-farm' } })
    expect(map.props('selectedSlug')).toBe('cau-dat-farm')
    expect(wrapper.get('#map-selected-title').text()).toBe('Cầu Đất Farm')
    expect(wrapper.get('.map-info-overlay').text()).toContain('HTX Chè Cầu Đất')
    expect(wrapper.get('.map-info-overlay').text()).toContain('Trà xanh Cầu Đất')
    expect(wrapper.get('.external-directions').attributes('href')).toContain('11.879583%2C108.547398')

    map.vm.$emit('select', 'vuon-hong-nha-tom')
    await flushPromises()
    expect(wrapper.get('#map-selected-title').text()).toBe('Vườn hồng Nhà Tom')
  })

  it('chon san diem tu query va bo qua slug khong ton tai', async () => {
    route.query = { diem: 'vuon-hong-nha-tom' }
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.get('#map-selected-title').text()).toBe('Vườn hồng Nhà Tom')

    route.query = { diem: 'khong-ton-tai' }
    vi.mocked(getMapLocations).mockResolvedValueOnce({ type: 'FeatureCollection', features })
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('#map-selected-title').exists()).toBe(false)
  })
  it('normal destination focuses marker without route intent or automatic GPS', async () => {
    const gps = mockGeolocation({ latitude: 11.9404, longitude: 108.4383 })
    route.query = { diem: 'cau-dat-farm' }
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.getComponent(LeafletMapStub).props('selectedSlug')).toBe('cau-dat-farm')
    expect(wrapper.find('[data-test="route-intent"]').exists()).toBe(false)
    expect(gps).not.toHaveBeenCalled()
    expect(getRoute).not.toHaveBeenCalled()
  })
  it('route intent selects destination and waits for explicit GPS confirmation before routing', async () => {
    const origin = { latitude: 11.9404, longitude: 108.4383 }
    const gps = mockGeolocation(origin)
    vi.mocked(getNearbyLocations).mockResolvedValue({ origin, radius_m: 50000, items: [] })
    vi.mocked(getRoute).mockResolvedValue({ provider: 'OSRM', profile: 'driving', origin,
      destination: { slug: 'cau-dat-farm', name: 'Cầu Đất Farm', latitude: 11.879583, longitude: 108.547398 },
      distance_m: 1000, duration_s: 120, geometry: { type: 'LineString', coordinates: [[108.4383, 11.9404], [108.547398, 11.879583]] },
    })
    route.query = { diem: 'cau-dat-farm', action: 'route' }
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.getComponent(LeafletMapStub).props('selectedSlug')).toBe('cau-dat-farm')
    expect(wrapper.get('[data-test="route-intent"]').text()).toContain('xác nhận')
    expect(gps).not.toHaveBeenCalled()
    expect(getRoute).not.toHaveBeenCalled()
    await wrapper.get('.map-info-actions button').trigger('click')
    await flushPromises()
    expect(gps).toHaveBeenCalledTimes(1)
    expect(getRoute).toHaveBeenCalledWith('cau-dat-farm', origin)
    expect(wrapper.find('.route-summary').exists()).toBe(true)
    expect(wrapper.find('[data-test="route-intent"]').exists()).toBe(false)
    wrapper.getComponent(LeafletMapStub).vm.$emit('select', 'vuon-hong-nha-tom')
    await flushPromises()
    expect(wrapper.find('[data-test="route-intent"]').exists()).toBe(false)
  })
  it('route intent respects denied GPS permission without requesting a route', async () => {
    const gps = mockGeolocation({ code: 1 })
    route.query = { diem: 'cau-dat-farm', action: 'route' }
    const wrapper = mountView()
    await flushPromises()
    expect(gps).not.toHaveBeenCalled()
    await wrapper.get('.map-info-actions button').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Bạn chưa cho phép truy cập vị trí')
    expect(getRoute).not.toHaveBeenCalled()
    expect(wrapper.find('[data-test="route-intent"]').exists()).toBe(true)
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
      { radiusKm: 50, limit: 5, type: undefined, kind: 'all' },
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

    const routeButton = wrapper.findAll('.map-info-actions button')[0]
    await routeButton.trigger('click')
    await flushPromises()

    expect(getRoute).toHaveBeenCalledWith('cau-dat-farm', { latitude: 11.9404, longitude: 108.4383 })
    expect(wrapper.findAll('.route-summary')).toHaveLength(1)
    expect(wrapper.find('.map-info-overlay .route-summary').exists()).toBe(true)
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

    await wrapper.findAll('.map-info-actions button')[0].trigger('click')
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

  it('khoi phuc bo loc tu URL va goi API voi dung tham so', async () => {
    route.query = { type: 'tea_coffee_farm', district: 'Đà Lạt', search: 'chè', diem: 'cau-dat-farm' }
    const wrapper = mountView()
    await flushPromises()

    expect(getMapLocations).toHaveBeenCalledWith({ search: 'chè', type: 'tea_coffee_farm', district: 'Đà Lạt' })
    expect((wrapper.get('#map-search').element as HTMLInputElement).value).toBe('chè')
    expect((wrapper.get('select[aria-label="Lọc theo loại hình"]').element as HTMLSelectElement).value).toBe('tea_coffee_farm')
    expect((wrapper.get('select[aria-label="Lọc theo địa bàn"]').element as HTMLSelectElement).value).toBe('Đà Lạt')
    expect(wrapper.get('#map-selected-title').text()).toBe('Cầu Đất Farm')
  })

  it('ghi bo loc len URL, giu tham so diem; tim kiem dung replace, chon select dung push', async () => {
    route.query = { diem: 'cau-dat-farm' }
    const wrapper = mountView()
    await flushPromises()

    await wrapper.get('#map-search').setValue('  dâu  ')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(router.replace).toHaveBeenLastCalledWith({ name: 'map', query: { diem: 'cau-dat-farm', search: 'dâu' } })
    expect(getMapLocations).toHaveBeenLastCalledWith({ search: 'dâu', type: undefined, district: undefined })

    route.query = { diem: 'cau-dat-farm', search: 'dâu' }
    await wrapper.get('select[aria-label="Lọc theo loại hình"]').setValue('tea_coffee_farm')
    await flushPromises()
    expect(router.push).toHaveBeenLastCalledWith({
      name: 'map',
      query: { diem: 'cau-dat-farm', search: 'dâu', type: 'tea_coffee_farm' },
    })
  })

  it('chon diem giu nguyen cac bo loc trong URL', async () => {
    route.query = { type: 'tea_coffee_farm', district: 'Đà Lạt' }
    const wrapper = mountView()
    await flushPromises()
    await wrapper.findAll('.location-list button')[1].trigger('click')
    expect(router.replace).toHaveBeenLastCalledWith({
      name: 'map',
      query: { type: 'tea_coffee_farm', district: 'Đà Lạt', diem: 'vuon-hong-nha-tom' },
    })
  })

  it('doi URL (Back) thi bo loc va du lieu duoc dong bo theo', async () => {
    const wrapper = mountView()
    await flushPromises()
    vi.mocked(getMapLocations).mockClear()

    route.query = { type: 'tea_coffee_farm' }
    await flushPromises()
    expect(getMapLocations).toHaveBeenCalledTimes(1)
    expect(getMapLocations).toHaveBeenCalledWith({ search: undefined, type: 'tea_coffee_farm', district: undefined })
    expect((wrapper.get('select[aria-label="Lọc theo loại hình"]').element as HTMLSelectElement).value).toBe('tea_coffee_farm')
  })

  it('khong co ket qua thi co nut Xoa bo loc dua ve trang thai goc', async () => {
    vi.mocked(getMapLocations).mockResolvedValue({ type: 'FeatureCollection', features: [] })
    route.query = { search: 'khongco' }
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('Không có địa điểm phù hợp với bộ lọc')

    vi.mocked(getMapLocations).mockResolvedValue({ type: 'FeatureCollection', features })
    await wrapper.get('.empty-state button').trigger('click')
    await flushPromises()
    expect(router.push).toHaveBeenLastCalledWith({ name: 'map', query: {} })
    expect(getMapLocations).toHaveBeenLastCalledWith({ search: undefined, type: undefined, district: undefined })
    expect((wrapper.get('#map-search').element as HTMLInputElement).value).toBe('')
  })

  it('diem toa do null hoac [0,0] van co trong danh sach, thong bao dem so diem chua ve duoc', async () => {
    const bad = [
      ...features,
      { ...feature('khong-toa-do', 'Không tọa độ', [0, 0]), geometry: { type: 'Point', coordinates: null } } as unknown as MapFeature,
      feature('zero', 'Điểm 0,0', [0, 0]),
    ]
    vi.mocked(getMapLocations).mockResolvedValue({ type: 'FeatureCollection', features: bad })
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('2 địa điểm đang hiển thị trên bản đồ')
    expect(wrapper.get('[data-test="unmappable-notice"]').text()).toContain('2 điểm chưa có tọa độ hợp lệ nên chưa hiển thị trên bản đồ')
    expect(wrapper.get('[data-test="unmappable-notice"]').attributes('role')).toBe('status')
    expect(wrapper.findAll('.location-list button')).toHaveLength(4)

    await wrapper.findAll('.location-list button')[2].trigger('click')
    expect(wrapper.get('#map-selected-title').text()).toBe('Không tọa độ')
    expect(wrapper.find('[data-test="no-coordinates"]').exists()).toBe(true)
    expect(wrapper.find('.external-directions').exists()).toBe(false)
    expect(wrapper.find('.map-info-actions .btn-success').exists()).toBe(false)
  })

  it('chu giai loc theo loai hinh va dong bo voi URL', async () => {
    const wrapper = mountView()
    await flushPromises()
    const legend = wrapper.findAll('button.legend-item')
    expect(legend).toHaveLength(1)
    expect(legend[0].text()).toContain('2')
    await legend[0].trigger('click')
    await flushPromises()
    expect(router.push).toHaveBeenLastCalledWith({ name: 'map', query: { type: 'tea_coffee_farm' } })
    expect(getMapLocations).toHaveBeenLastCalledWith({ search: undefined, type: 'tea_coffee_farm', district: undefined })
  })

  it('Diem gan ban ap bo loc loai hinh qua API, dia ban va tu khoa o phia client', async () => {
    mockGeolocation({ latitude: 11.9404, longitude: 108.4383 })
    const outside = { ...nearbyItem, id: 8, name: 'Nhà vườn Đức Trọng', slug: 'duc-trong', district: 'Đức Trọng' }
    vi.mocked(getNearbyLocations).mockResolvedValue({
      origin: { latitude: 11.9404, longitude: 108.4383 }, radius_m: 50000, items: [outside, nearbyItem],
    })
    route.query = { type: 'fruit_garden', district: 'Đà Lạt' }
    const wrapper = mountView()
    await flushPromises()
    await wrapper.get('button.btn-outline-success').trigger('click')
    await flushPromises()

    expect(getNearbyLocations).toHaveBeenLastCalledWith(
      { latitude: 11.9404, longitude: 108.4383 },
      { radiusKm: 50, limit: 50, type: 'fruit_garden', kind: 'all' },
    )
    const names = wrapper.findAll('.nearby-list li').map((item) => item.text())
    expect(names).toHaveLength(1)
    expect(names[0]).toContain('Vườn hồng Nhà Tom')
  })

  it('chon diem gan ban nam ngoai bo loc van hien the va ban do, kem thong bao', async () => {
    mockGeolocation({ latitude: 11.9404, longitude: 108.4383 })
    const extra = { ...nearbyItem, id: 9, name: 'Điểm ngoài lọc', slug: 'ngoai-loc' }
    vi.mocked(getNearbyLocations).mockResolvedValue({
      origin: { latitude: 11.9404, longitude: 108.4383 }, radius_m: 50000, items: [extra],
    })
    const wrapper = mountView()
    await flushPromises()
    await wrapper.get('button.btn-outline-success').trigger('click')
    await flushPromises()
    await wrapper.get('.nearby-list button').trigger('click')
    await flushPromises()

    expect(wrapper.get('#map-selected-title').text()).toBe('Điểm ngoài lọc')
    expect(wrapper.find('[data-test="outside-filter"]').exists()).toBe(true)
    const map = wrapper.getComponent(LeafletMapStub)
    expect(map.props('selectedSlug')).toBe('ngoai-loc')
    expect((map.props('features') as MapFeature[]).map((item) => item.properties.slug)).toContain('ngoai-loc')
    expect(router.replace).toHaveBeenLastCalledWith({ name: 'map', query: { diem: 'ngoai-loc' } })

    // Chon diem khac trong danh sach thi diem tam bi go khoi tap ve
    await wrapper.findAll('.location-list button')[0].trigger('click')
    expect((map.props('features') as MapFeature[]).map((item) => item.properties.slug)).not.toContain('ngoai-loc')
  })

  it('chon ban kinh gan ban va dung thong bao khi ngoai Lam Dong', async () => {
    mockGeolocation({ latitude: 21.03, longitude: 105.85 })
    vi.mocked(getNearbyLocations).mockResolvedValue({
      origin: { latitude: 21.03, longitude: 105.85 }, radius_m: 50000, items: [],
    })
    const wrapper = mountView()
    await flushPromises()
    await wrapper.get('button.btn-outline-success').trigger('click')
    await flushPromises()
    expect(wrapper.get('.panel-message').text()).toContain('Bạn đang ở ngoài Lâm Đồng')
    expect(wrapper.get('.panel-message').text()).toContain('bán kính 50 km')

    await wrapper.get('#nearby-radius').setValue(100)
    await flushPromises()
    expect(getNearbyLocations).toHaveBeenLastCalledWith(
      { latitude: 21.03, longitude: 105.85 },
      { radiusKm: 100, limit: 5, type: undefined, kind: 'all' },
    )
  })

  it('chi dan hang loat mot thong bao khi Chi duong ma bi tu choi vi tri', async () => {
    mockGeolocation({ code: 1 })
    route.query = { diem: 'cau-dat-farm' }
    const wrapper = mountView()
    await flushPromises()
    await wrapper.get('.map-info-actions .btn-success').trigger('click')
    await flushPromises()

    expect(wrapper.findAll('.panel-message')).toHaveLength(1)
    expect(wrapper.get('.map-info-overlay .panel-message').text()).toContain('Bạn chưa cho phép truy cập vị trí')
    expect(getRoute).not.toHaveBeenCalled()
  })

  it('phim Esc bo chon diem nhung khong khi dang go trong o nhap', async () => {
    route.query = { diem: 'cau-dat-farm' }
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.find('#map-selected-title').exists()).toBe(true)

    wrapper.get('#map-search').element.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    await flushPromises()
    expect(wrapper.find('#map-selected-title').exists()).toBe(true)

    document.body.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    await flushPromises()
    expect(wrapper.find('#map-selected-title').exists()).toBe(false)
    expect(router.replace).toHaveBeenLastCalledWith({ name: 'map', query: {} })
  })
  describe('lop diem du lich va cua hang, loc theo san pham va chu the', () => {
    const mixed = [
      feature('cau-dat-farm', 'Cầu Đất Farm', [108.547398, 11.879583]),
      shopFeature('cua-hang-yersin', 'Cửa hàng Yersin', [108.4494, 11.9430], 'sold_here'),
      shopFeature('co-so-pang-tieng', 'Cơ sở Păng Tiêng', [108.3474, 11.9908], 'produced_here'),
    ]

    beforeEach(() => {
      vi.mocked(getMapLocations).mockResolvedValue({ type: 'FeatureCollection', features: mixed })
    })

    it('dem so diem moi lop va chuyen lop ma khong tai lai ban do', async () => {
      const wrapper = mountView()
      await flushPromises()
      const map = wrapper.getComponent(LeafletMapStub)
      expect(map.props('features')).toHaveLength(3)
      expect(wrapper.get('[data-kind="shop"]').text()).toContain('2')
      expect(wrapper.get('[data-kind="attraction"]').text()).toContain('1')

      vi.mocked(getMapLocations).mockClear()
      await wrapper.get('[data-kind="shop"]').trigger('click')
      await flushPromises()

      expect(getMapLocations).not.toHaveBeenCalled()
      expect(map.props('features').map((item: MapFeature) => item.properties.slug)).toEqual([
        'cua-hang-yersin',
        'co-so-pang-tieng',
      ])
      expect(wrapper.get('[data-kind="shop"]').attributes('aria-pressed')).toBe('true')
      expect(router.push).toHaveBeenCalledWith({ name: 'map', query: { kind: 'shop' } })
    })

    it('doc lop tu URL va hien thong tin lien he cua cua hang da chon', async () => {
      route.query = { kind: 'shop', diem: 'cua-hang-yersin' }
      const wrapper = mountView()
      await flushPromises()

      expect(wrapper.getComponent(LeafletMapStub).props('features')).toHaveLength(2)
      const card = wrapper.get('.map-info-overlay')
      expect(card.text()).toContain('Cửa hàng OCOP')
      expect(card.get('a[href="tel:02633798888"]').text()).toContain('0263 379 8888')
      expect(card.get('a[href="https://example.com/"]').attributes('rel')).toContain('noopener')
      expect(card.text()).toContain('Bán tại đây')
      expect(card.text()).not.toContain('Vé:')
    })

    it('loc theo san pham: tra san pham, gui product_id, hien nhan vai tro va noi san xuat voi noi ban', async () => {
      route.query = { product: 'dau-tay-say-deo' }
      vi.mocked(getProductLocations).mockResolvedValue({
        product_id: 10,
        product_name: 'Dâu tây sấy dẻo',
        product_slug: 'dau-tay-say-deo',
        items: [],
      })
      const wrapper = mountView()
      await flushPromises()

      expect(getProductLocations).toHaveBeenCalledWith('dau-tay-say-deo')
      expect(getMapLocations).toHaveBeenLastCalledWith(expect.objectContaining({ product_id: 10 }))
      expect(wrapper.get('[data-test="context-banner"]').text()).toContain('Dâu tây sấy dẻo')
      const badges = wrapper.findAll('[data-test="role-badge"]').map((badge) => badge.text())
      expect(badges).toEqual(['Bán tại đây', 'Sản xuất tại đây'])
      expect(wrapper.getComponent(LeafletMapStub).props('links')).toEqual([['co-so-pang-tieng', 'cua-hang-yersin']])

      vi.mocked(getMapLocations).mockClear()
      await wrapper.get('[data-test="clear-context"]').trigger('click')
      await flushPromises()
      expect(router.push).toHaveBeenCalledWith({ name: 'map', query: {} })
      expect(getMapLocations).toHaveBeenLastCalledWith(expect.objectContaining({ product_id: undefined }))
    })

    it('loc theo chu the: gui subject_id va hien so diem, so san pham', async () => {
      route.query = { subject: '1' }
      vi.mocked(getPublicSubject).mockResolvedValue({
        id: 1,
        name: 'HTX Chè Cầu Đất',
        district: 'Đà Lạt',
        address: 'Đà Lạt',
        locations: [],
        products: [],
      })
      const wrapper = mountView()
      await flushPromises()

      expect(getPublicSubject).toHaveBeenCalledWith(1)
      expect(getMapLocations).toHaveBeenLastCalledWith(expect.objectContaining({ subject_id: 1 }))
      expect(wrapper.get('[data-test="context-banner"]').text()).toContain('HTX Chè Cầu Đất')
    })

    it('san pham khong con cong khai thi bo loc va bao cho nguoi dung', async () => {
      route.query = { product: 'khong-ton-tai' }
      vi.mocked(getProductLocations).mockRejectedValue(new Error('404'))
      const wrapper = mountView()
      await flushPromises()

      expect(wrapper.find('[data-test="context-banner"]').exists()).toBe(false)
      expect(wrapper.get('[data-test="context-message"]').text()).toContain('Không tìm thấy sản phẩm')
      expect(getMapLocations).toHaveBeenLastCalledWith(expect.objectContaining({ product_id: undefined }))
      expect(wrapper.getComponent(LeafletMapStub).props('features')).toHaveLength(3)
    })

    it('chip nhom san pham gui category len may chu', async () => {
      const wrapper = mountView()
      await flushPromises()

      await wrapper.get('[data-test="category-chip"]').trigger('click')
      await flushPromises()

      expect(getMapLocations).toHaveBeenLastCalledWith(expect.objectContaining({ category: 'do-uong' }))
      expect(router.push).toHaveBeenCalledWith({ name: 'map', query: { category: 'do-uong' } })
    })

    it('tuyen tham quan: liet ke tuyen, chon tuyen chi hien cac chang va noi theo thu tu', async () => {
      vi.mocked(getTours).mockResolvedValue([
        { id: 1, slug: 'hanh-trinh-dau-tay', name: 'Hành trình dâu tây', description: null, duration_text: 'Nửa ngày', stop_count: 2 },
      ])
      vi.mocked(getTour).mockResolvedValue({
        id: 1,
        slug: 'hanh-trinh-dau-tay',
        name: 'Hành trình dâu tây',
        description: 'Gợi ý của nhóm.',
        duration_text: 'Nửa ngày',
        stop_count: 2,
        stops: [
          { position: 1, note: 'Nơi sản xuất', location: { ...mixed[2].properties, latitude: 11.99, longitude: 108.34 } as never },
          { position: 2, note: 'Mua quà', location: { ...mixed[1].properties, latitude: 11.94, longitude: 108.44 } as never },
        ],
      })
      const wrapper = mountView()
      await flushPromises()

      expect(wrapper.get('[data-test="tour-item"]').text()).toContain('2 chặng · Nửa ngày')
      await wrapper.get('[data-test="tour-item"]').trigger('click')
      await flushPromises()

      expect(router.push).toHaveBeenCalledWith({ name: 'map', query: { tour: 'hanh-trinh-dau-tay' } })
      expect(getTour).toHaveBeenCalledWith('hanh-trinh-dau-tay')
      const map = wrapper.getComponent(LeafletMapStub)
      expect(map.props('features').map((item: MapFeature) => item.properties.slug)).toEqual(['cua-hang-yersin', 'co-so-pang-tieng'])
      expect(map.props('links')).toEqual([['co-so-pang-tieng', 'cua-hang-yersin']])
      const stops = wrapper.get('[data-test="tour-stops"]').findAll('li')
      expect(stops).toHaveLength(2)
      expect(stops[0]!.text()).toContain('Cơ sở Păng Tiêng')
      expect(stops[0]!.text()).toContain('Nơi sản xuất')
      expect(wrapper.find('[data-test="tour-list"]').exists()).toBe(false)
    })

    it('tuyen khong con cong khai thi bo loc tuyen va bao cho nguoi dung', async () => {
      route.query = { tour: 'khong-ton-tai' }
      vi.mocked(getTour).mockRejectedValue(new Error('404'))
      const wrapper = mountView()
      await flushPromises()

      expect(wrapper.get('[data-test="context-message"]').text()).toContain('Không tìm thấy tuyến')
      expect(wrapper.getComponent(LeafletMapStub).props('features')).toHaveLength(3)
    })

    it('che do Chi tiet hien dia chi, mo ta va dich vu trong danh sach', async () => {
      const wrapper = mountView()
      await flushPromises()
      expect(wrapper.find('.location-address').exists()).toBe(false)

      await wrapper.get('[data-test="view-detail"]').trigger('click')

      expect(wrapper.find('.location-list.is-detail').exists()).toBe(true)
      expect(wrapper.findAll('.location-address').length).toBe(3)
    })
  })
})
