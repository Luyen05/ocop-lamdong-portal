// @vitest-environment jsdom
import { AxiosError, AxiosHeaders } from 'axios'
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, reactive } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import LocationDetailView from '@/views/LocationDetailView.vue'
import { getLocation } from '@/services/locations'
import type { LocationDetail } from '@/types/location'

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

const mountView = () =>
  mount(LocationDetailView, {
    global: {
      stubs: {
        RouterLink: { props: ['to'], template: '<a><slot /></a>' },
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
})
