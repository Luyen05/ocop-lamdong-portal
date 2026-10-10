// @vitest-environment jsdom
import { AxiosError, AxiosHeaders } from 'axios'
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { defineComponent, reactive } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import LocationDetailView from '@/views/LocationDetailView.vue'
import { getLocation } from '@/services/locations'
import type { LocationDetail } from '@/types/location'

enableAutoUnmount(afterEach)

const route = reactive({ params: { slug: 'cau-dat-farm' } })

vi.mock('vue-router', () => ({
  useRoute: () => route,
}))

vi.mock('@/services/locations', () => ({
  getLocation: vi.fn(),
}))

const detail: LocationDetail = {
  id: 1,
  name: 'Cầu Đất Farm',
  slug: 'cau-dat-farm',
  type: 'tea_coffee_farm',
  type_label: 'Đồi chè & cà phê',
  district: 'Đà Lạt',
  address: 'Xuân Trường, Đà Lạt',
  latitude: 11.879583,
  longitude: 108.547398,
  opening_hours: '07:00 - 19:00',
  ticket_price: 0,
  services: ['Tham quan đồi chè', 'Chụp ảnh'],
  description: 'Đồi chè lâu năm.',
  rating_avg: 0,
  primary_image_url: null,
  contact_phone: '0943 268 138',
  website: 'javascript:alert(1)',
  source_url: 'https://www.foody.vn/lam-dong/doi-che-cau-dat',
  views: 0,
  images: [],
  subject: { id: 1, name: 'HTX Chè Cầu Đất', district: 'Đà Lạt' },
  products: [],
  updated_at: '2026-09-23T00:00:00Z',
}

const LeafletMapStub = defineComponent({
  name: 'LeafletMap',
  props: ['features', 'selectedSlug', 'cluster', 'initialZoom', 'label'],
  template: '<div class="map-stub" />',
})

const RouterLinkStub = defineComponent({ name: 'RouterLink', props: ['to'], template: '<a><slot /></a>' })

const mountView = () =>
  mount(LocationDetailView, {
    global: {
      stubs: {
        RouterLink: RouterLinkStub,
        LeafletMap: LeafletMapStub,
        ProductCard: true,
      },
    },
  })

describe('LocationDetailView', () => {
  beforeEach(() => vi.clearAllMocks())

  it('hien thi thong tin lien he, dich vu, nguon va ban do', async () => {
    vi.mocked(getLocation).mockResolvedValue(detail)
    const wrapper = mountView()
    await flushPromises()

    expect(getLocation).toHaveBeenCalledWith('cau-dat-farm')
    expect(wrapper.get('h1').text()).toBe('Cầu Đất Farm')
    expect(wrapper.text()).toContain('Miễn phí')
    expect(wrapper.text()).toContain('HTX Chè Cầu Đất')
    expect(wrapper.get('a[href^="tel:"]').attributes('href')).toBe('tel:0943268138')
    expect(wrapper.findAll('.service-list li')).toHaveLength(2)
    expect(wrapper.find('a[href="javascript:alert(1)"]').exists()).toBe(false)
    expect(wrapper.get('a[href="https://www.foody.vn/lam-dong/doi-che-cau-dat"]').attributes('rel')).toContain('noopener')
    expect(wrapper.get('a[href*="google.com/maps/dir"]').attributes('href')).toContain('11.879583%2C108.547398')
    const map = wrapper.getComponent(LeafletMapStub)
    expect(map.props('features')[0].geometry.coordinates).toEqual([108.547398, 11.879583])
  })

  it('bao khong tim thay khi api tra 404', async () => {
    vi.mocked(getLocation).mockRejectedValue(
      new AxiosError('Not found', 'ERR_BAD_REQUEST', undefined, undefined, {
        status: 404,
        statusText: 'Not Found',
        headers: {},
        config: { headers: new AxiosHeaders() },
        data: { code: 'LOCATION_NOT_FOUND', message: 'Không tìm thấy điểm du lịch.', details: null },
      }),
    )
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.get('h1').text()).toBe('Không tìm thấy điểm du lịch')
    expect(wrapper.text()).toContain('Không tìm thấy điểm du lịch.')
  })
  it('keeps missing imagery compact and separates selected map from external directions', async () => {
    vi.mocked(getLocation).mockResolvedValue(detail)
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.get('.gallery').classes()).toContain('without-image')
    expect(wrapper.get('.image-placeholder').text()).toBe('Ảnh điểm đến đang cập nhật')
    expect(wrapper.find('.main-image img').exists()).toBe(false)
    const mapLink = wrapper.findAllComponents(RouterLinkStub).find(link => link.props('to')?.name === 'map')
    expect(mapLink?.props('to')).toEqual({ name: 'map', query: { diem: detail.slug } })
    expect(wrapper.get('a[href*="google.com/maps/dir"]').attributes('target')).toBe('_blank')
  })
  it('renders real gallery attribution and product relations supplied by API', async () => {
    const related = {
      id: 7, name: 'Sản phẩm tại điểm đến', slug: 'san-pham-tai-diem-den', star: 4,
      price: null, unit: null, description: '', rating_avg: 0, vietgap_code: null, primary_image_url: null,
      category: { id: 1, name: 'Đồ uống', slug: 'do-uong' },
      subject: { id: 1, name: 'Chủ thể', district: 'Đà Lạt' }, created_at: '',
    }
    vi.mocked(getLocation).mockResolvedValue({ ...detail, products: [related], images: [
      { id: 1, image_url: 'https://example.com/farm.jpg', is_primary: true, sort_order: 0,
        source_url: 'https://example.com/source', credit: 'Chủ điểm đến', license: 'Được cho phép' },
    ] })
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.get('.main-image img').attributes('src')).toBe('https://example.com/farm.jpg')
    expect(wrapper.get('.main-image img').attributes('alt')).toBe(detail.name)
    expect(wrapper.get('.image-credit').text()).toContain('Chủ điểm đến')
    expect(wrapper.get('#location-products-title').text()).toBe('Sản phẩm OCOP tại điểm này')
    expect(wrapper.getComponent({ name: 'ProductCard' }).props('product')).toEqual(related)
    expect(wrapper.get('.product-grid').classes()).toContain('product-grid-spacious')
    expect(wrapper.get('.related-product-cta').text()).toBe('Xem sản phẩm')
    const productLink = wrapper.findAllComponents(RouterLinkStub).find(link => link.classes().includes('related-product-cta'))
    expect(productLink?.props('to')).toEqual({ name: 'product-detail', params: { slug: related.slug } })
    await wrapper.get('.main-image img').trigger('error')
    expect(wrapper.find('.image-placeholder').exists()).toBe(true)
    expect(wrapper.find('.image-credit').exists()).toBe(false)
  })
})
