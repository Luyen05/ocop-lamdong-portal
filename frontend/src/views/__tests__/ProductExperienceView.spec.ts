// @vitest-environment jsdom
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import appRouter from '@/router'
import ProductExperienceView from '@/views/ProductExperienceView.vue'
import { getProduct } from '@/services/products'
import { getLocation, getNearbyLocations } from '@/services/locations'
import type { ProductDetail } from '@/types/product'
import type { LocationDetail } from '@/types/location'

vi.mock('@/services/products', () => ({ getProduct: vi.fn(), getProducts: vi.fn() }))
vi.mock('@/services/locations', () => ({ getLocation: vi.fn(), getNearbyLocations: vi.fn() }))
enableAutoUnmount(afterEach)

const relations = [
  { id: 1, slug: 'showroom-a', name: 'Showroom A', type_label: 'Điểm trải nghiệm', district: 'Đà Lạt' },
  { id: 2, slug: 'showroom-b', name: 'Showroom B', type_label: 'Điểm trải nghiệm', district: 'Đà Lạt' },
  { id: 3, slug: 'showroom-c', name: 'Showroom C', type_label: 'Điểm trải nghiệm', district: 'Đà Lạt' },
]
const product: ProductDetail = {
  id: 10, slug: 'ca-phe-demo', name: 'Cà phê demo', star: 4, price: null, unit: null,
  description: '', rating_avg: 0, vietgap_code: null, primary_image_url: null,
  category: { id: 1, slug: 'do-uong', name: 'Đồ uống' },
  subject: { id: 1, name: 'Chủ thể demo', district: 'Đà Lạt' },
  created_at: '', updated_at: '', cert_code: null, cert_year: null, cert_issued_at: null,
  cert_expires_at: null, issuing_authority: null, story: null, ingredients: null,
  usage_instructions: null, views: 0, images: [], recognition_sources: [], related_locations: relations,
}
function detail(index: number): LocationDetail {
  return {
    ...relations[index]!, type: 'other', address: `Địa chỉ ${index + 1}`,
    latitude: 11.9, longitude: 108.4, services: ['Thử cà phê'], opening_hours: null,
    ticket_price: null, description: null, rating_avg: 0, primary_image_url: null,
    contact_phone: null, website: null, source_url: null, views: 0, images: [],
    subject: null, products: [], updated_at: '',
  }
}
const origin = { latitude: 11.9, longitude: 108.4 }
const getCurrentPosition = vi.fn()

async function mountPage() {
  const router = createRouter({ history: createMemoryHistory(), routes: appRouter.options.routes })
  await router.push(`/san-pham/${product.slug}/diem-trai-nghiem`)
  await router.isReady()
  const wrapper = mount(ProductExperienceView, { global: { plugins: [router] } })
  await flushPromises()
  return { wrapper, router }
}

beforeEach(() => {
  vi.resetAllMocks()
  vi.mocked(getProduct).mockResolvedValue(product)
  vi.mocked(getLocation).mockImplementation(async (slug) => detail(relations.findIndex((r) => r.slug === slug)))
  vi.mocked(getNearbyLocations).mockResolvedValue({ origin, radius_m: 200000, items: [] })
  getCurrentPosition.mockImplementation((success: PositionCallback) => success({ coords: origin } as GeolocationPosition))
  Object.defineProperty(navigator, 'geolocation', { configurable: true, value: { getCurrentPosition } })
})

describe('Product Experience Finder', () => {
  it('registers its route and loads the product by slug', async () => {
    const { wrapper, router } = await mountPage()
    expect(router.currentRoute.value.name).toBe('product-experience')
    expect(router.currentRoute.value.matched[0]?.components?.default).toBe(ProductExperienceView)
    expect(getProduct).toHaveBeenCalledWith(product.slug)
    expect(wrapper.text()).toContain(product.name)
    expect(wrapper.text()).toContain('4 sao OCOP')
    expect(wrapper.text()).toContain('Chủ thể demo')
  })
  it('renders only verified relations with address, type and services', async () => {
    const { wrapper } = await mountPage()
    expect(wrapper.findAll('.experience-location')).toHaveLength(3)
    expect(wrapper.text()).toContain('Địa chỉ 1')
    expect(wrapper.text()).toContain('Thử cà phê')
    expect(wrapper.text()).toContain('Điểm trải nghiệm')
    expect(getLocation).toHaveBeenCalledTimes(3)
  })
  it.each([[], undefined])('shows empty state without discovering other relations (%s)', async (related_locations) => {
    vi.mocked(getProduct).mockResolvedValue({ ...product, related_locations })
    const { wrapper } = await mountPage()
    expect(wrapper.text()).toContain('Hiện chưa có điểm mua/trải nghiệm được xác minh cho sản phẩm này.')
    expect(wrapper.find('[data-test="locate"]').exists()).toBe(false)
    expect(getLocation).not.toHaveBeenCalled()
    expect(getNearbyLocations).not.toHaveBeenCalled()
    expect(getCurrentPosition).not.toHaveBeenCalled()
  })
  it('does not request GPS on load; requests only on click and shows loading', async () => {
    const { wrapper } = await mountPage()
    expect(getCurrentPosition).not.toHaveBeenCalled()
    expect(getNearbyLocations).not.toHaveBeenCalled()
    getCurrentPosition.mockImplementation(() => {})
    await wrapper.get('[data-test="locate"]').trigger('click')
    expect(getCurrentPosition).toHaveBeenCalledTimes(1)
    expect(wrapper.get('[data-test="locate"]').attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Đang tìm điểm gần bạn')
  })
  it('intersects Nearby by id/slug, sorts distances, keeps unmatched relations last', async () => {
    vi.mocked(getNearbyLocations).mockResolvedValue({ origin, radius_m: 200000, items: [
      { ...detail(0), distance_m: 900 },
      { ...detail(1), distance_m: 100 },
      { ...detail(2), id: 999, slug: 'unrelated', name: 'Không liên quan', distance_m: 1 },
    ] })
    const { wrapper } = await mountPage()
    await wrapper.get('[data-test="locate"]').trigger('click')
    await flushPromises()
    expect(getNearbyLocations).toHaveBeenCalledWith(origin, { radiusKm: 200, limit: 50 })
    expect(wrapper.findAll('.experience-location h3').map((node) => node.text())).toEqual(['Showroom B', 'Showroom A', 'Showroom C'])
    expect(wrapper.text()).not.toContain('Không liên quan')
    expect(wrapper.text()).toContain('100 m')
    expect(wrapper.text()).toContain('900 m')
    expect(wrapper.text()).toContain('Chưa có khoảng cách')
  })
  it.each([1, 2, 3])('handles geolocation errors (%s) without Nearby call', async (code) => {
    getCurrentPosition.mockImplementation((_success: PositionCallback, failure: PositionErrorCallback) => {
      failure({ code, PERMISSION_DENIED: 1, TIMEOUT: 3 } as GeolocationPositionError)
    })
    const { wrapper } = await mountPage()
    await wrapper.get('[data-test="locate"]').trigger('click')
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain(code === 1 ? 'Bạn chưa cho phép' : code === 3 ? 'Hết thời gian' : 'Không xác định được')
    expect(getNearbyLocations).not.toHaveBeenCalled()
    expect(wrapper.get('[data-test="locate"]').attributes('disabled')).toBeUndefined()
  })
  it('handles unsupported geolocation', async () => {
    Object.defineProperty(navigator, 'geolocation', { configurable: true, value: undefined })
    const { wrapper } = await mountPage()
    await wrapper.get('[data-test="locate"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Trình duyệt không hỗ trợ định vị')
  })
  it('keeps related cards on Nearby error and allows retry', async () => {
    vi.mocked(getNearbyLocations).mockRejectedValueOnce(new Error('offline'))
    const { wrapper } = await mountPage()
    await wrapper.get('[data-test="locate"]').trigger('click')
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('Không thể tìm điểm gần bạn')
    expect(wrapper.findAll('.experience-location')).toHaveLength(3)
    await wrapper.get('[data-test="locate"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
  })
  it('links map to a selected destination and directions to explicit route intent', async () => {
    const { wrapper, router } = await mountPage()
    const card = wrapper.get('.experience-location')
    expect(card.get('[data-test="detail"]').attributes('href')).toBe('/diem-du-lich/showroom-a')
    expect(card.get('[data-test="map"]').attributes('href')).toBe('/ban-do?diem=showroom-a')
    expect(card.get('[data-test="directions"]').attributes('href')).toBe('/ban-do?diem=showroom-a&action=route')
    expect(wrapper.text()).toContain('Chỉ đường mở bước xác nhận')
    expect(router.resolve(card.get('[data-test="directions"]').attributes('href')!).name).toBe('map')
    expect(getCurrentPosition).not.toHaveBeenCalled()
  })
  it('renders real location imagery, source credit, service chips and manager from API details', async () => {
    vi.mocked(getLocation).mockResolvedValue({
      ...detail(0),
      subject: { id: 9, name: 'Đơn vị quản lý A', district: 'Đà Lạt' },
      images: [{ id: 1, image_url: 'https://example.com/location.jpg', is_primary: true, sort_order: 0,
        source_url: 'https://example.com/location-source', credit: 'Chủ điểm đến', license: 'Được cho phép' }],
    })
    const { wrapper } = await mountPage()
    const card = wrapper.get('.experience-location')
    expect(card.get('.main-image img').attributes('src')).toBe('https://example.com/location.jpg')
    expect(card.get('.main-image img').attributes('alt')).toBe('Showroom A')
    expect(card.get('.image-credit').text()).toContain('Chủ điểm đến')
    expect(card.get('.service-chips li').text()).toBe('Thử cà phê')
    expect(card.get('.manager').text()).toContain('Đơn vị quản lý A')
    expect(getCurrentPosition).not.toHaveBeenCalled()
  })
  it('shows product loading then error with retry', async () => {
    let reject!: (error: Error) => void
    vi.mocked(getProduct).mockReturnValueOnce(new Promise((_resolve, fail) => { reject = fail }))
    const { wrapper } = await mountPage()
    expect(wrapper.text()).toContain('Đang tải sản phẩm')
    reject(new Error('offline'))
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('Không thể tải thông tin sản phẩm')
    await wrapper.get('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain(product.name)
  })
  it('keeps relation summary if location enrichment fails', async () => {
    vi.mocked(getLocation).mockRejectedValue(new Error('offline'))
    const { wrapper } = await mountPage()
    expect(wrapper.findAll('.experience-location')).toHaveLength(3)
    expect(wrapper.text()).toContain('Chưa tải được thông tin bổ sung')
    expect(wrapper.findAll('.location-media')).toHaveLength(3)
    expect(wrapper.get('.media-status').text()).toBe('Chưa tải được ảnh điểm đến.')
    expect(wrapper.get('.location-content').text()).toContain('Địa chỉ: Chưa tải được')
  })
  it('keeps media and content columns while location details are loading', async () => {
    vi.mocked(getLocation).mockReturnValue(new Promise(() => {}))
    const { wrapper } = await mountPage()
    expect(wrapper.get('.media-status').text()).toContain('Đang tải thông tin điểm đến')
    expect(wrapper.get('.location-content').text()).toContain('Địa chỉ: Đang tải...')
    expect(wrapper.find('[data-test="map"]').exists()).toBe(true)
    expect(getCurrentPosition).not.toHaveBeenCalled()
  })
  it('ignores stale product response after slug navigation', async () => {
    let resolve!: (value: ProductDetail) => void
    vi.mocked(getProduct).mockReturnValueOnce(new Promise((done) => { resolve = done }))
    const { wrapper, router } = await mountPage()
    vi.mocked(getProduct).mockResolvedValueOnce({ ...product, slug: 'new-product', name: 'Sản phẩm mới', related_locations: [] })
    await router.push('/san-pham/new-product/diem-trai-nghiem')
    await flushPromises()
    resolve(product)
    await flushPromises()
    expect(wrapper.get('h1').text()).toBe('Sản phẩm mới')
    expect(getLocation).not.toHaveBeenCalled()
  })
  it('ignores stale GPS result after navigating to product without relations', async () => {
    let success!: PositionCallback
    getCurrentPosition.mockImplementation((callback: PositionCallback) => { success = callback })
    const { wrapper, router } = await mountPage()
    await wrapper.get('[data-test="locate"]').trigger('click')
    vi.mocked(getProduct).mockResolvedValueOnce({ ...product, slug: 'empty', related_locations: [] })
    await router.push('/san-pham/empty/diem-trai-nghiem')
    await flushPromises()
    success({ coords: origin } as GeolocationPosition)
    await flushPromises()
    expect(getNearbyLocations).not.toHaveBeenCalled()
    expect(wrapper.findAll('.experience-location')).toHaveLength(0)
  })
})
