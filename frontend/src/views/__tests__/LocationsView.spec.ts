// @vitest-environment jsdom
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { reactive } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import LocationsView from '@/views/LocationsView.vue'
import { getLocationFilterOptions, getLocations } from '@/services/locations'
import type { LocationListItem } from '@/types/location'

const route = reactive({ query: {} as Record<string, string> })
const router = {
  push: vi.fn().mockResolvedValue(undefined),
  replace: vi.fn().mockResolvedValue(undefined),
}

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => router,
}))

vi.mock('@/services/locations', () => ({
  getLocations: vi.fn(),
  getLocationFilterOptions: vi.fn(),
}))

const location: LocationListItem = {
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
  ticket_price: 30000,
  services: ['Tham quan đồi chè'],
  description: 'Đồi chè lâu năm.',
  rating_avg: 0,
  primary_image_url: null,
}

enableAutoUnmount(afterEach)

const mountView = () =>
  mount(LocationsView, {
    global: { stubs: { RouterLink: { template: '<a><slot /></a>' }, LocationCard: true } },
  })

describe('LocationsView', () => {
  beforeEach(() => {
    route.query = {}
    vi.clearAllMocks()
    vi.mocked(getLocations).mockResolvedValue({ items: [location], page: 1, page_size: 12, total: 1 })
    vi.mocked(getLocationFilterOptions).mockResolvedValue({
      types: [{ value: 'tea_coffee_farm', label: 'Đồi chè & cà phê' }],
      districts: ['Lạc Dương', 'Đà Lạt', 'Bảo Lâm'],
    })
  })

  it('tai danh sach theo query va sap xep dia ban tieng Viet', async () => {
    route.query = { search: 'chè', type: 'tea_coffee_farm', district: 'Đà Lạt' }
    const wrapper = mountView()
    await flushPromises()

    expect(getLocations).toHaveBeenCalledWith({
      page: 1,
      page_size: 12,
      search: 'chè',
      type: 'tea_coffee_farm',
      district: 'Đà Lạt',
      sort: 'name',
    })
    expect(wrapper.findAll('#location-district option').map((option) => option.text())).toEqual([
      'Tất cả địa bàn',
      'Bảo Lâm',
      'Đà Lạt',
      'Lạc Dương',
    ])
    expect(wrapper.findAllComponents({ name: 'LocationCard' })).toHaveLength(1)
    expect(wrapper.text()).toContain('1 điểm du lịch phù hợp')
  })

  it('bo qua loai hinh khong hop le tren url', async () => {
    route.query = { type: 'casino' }
    mountView()
    await flushPromises()

    expect(vi.mocked(getLocations).mock.calls[0][0]).toMatchObject({ type: undefined })
  })

  it('hien thi trang thai rong va loi co nut thu lai', async () => {
    vi.mocked(getLocations).mockResolvedValueOnce({ items: [], page: 1, page_size: 12, total: 0 })
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('Chưa tìm thấy điểm du lịch phù hợp')

    vi.mocked(getLocations).mockRejectedValueOnce(new Error('network'))
    route.query = { search: 'dâu' }
    await flushPromises()
    expect(wrapper.find('[role="alert"]').text()).toContain('Không thể tải danh sách điểm du lịch')

    await wrapper.get('[role="alert"] button').trigger('click')
    await flushPromises()
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
  })

  it('day bo loc len url khi tim kiem', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.get('#location-search').setValue('  vườn dâu  ')
    await wrapper.get('form').trigger('submit')

    expect(router.push).toHaveBeenCalledWith({ name: 'locations', query: { search: 'vườn dâu' } })
  })
})
