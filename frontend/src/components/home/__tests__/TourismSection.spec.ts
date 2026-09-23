// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import TourismSection from '@/components/home/TourismSection.vue'
import { getLocations } from '@/services/locations'

vi.mock('@/services/locations', () => ({
  getLocations: vi.fn(),
}))

const stubs = { RouterLink: { template: '<a><slot /></a>' }, LocationCard: true }

describe('TourismSection', () => {
  beforeEach(() => vi.clearAllMocks())

  it('tai diem du lich that tu api thay cho du lieu minh hoa', async () => {
    vi.mocked(getLocations).mockResolvedValue({
      items: [
        {
          id: 1,
          name: 'Cầu Đất Farm',
          slug: 'cau-dat-farm',
          type: 'tea_coffee_farm',
          type_label: 'Đồi chè & cà phê',
          district: 'Đà Lạt',
          address: 'Xuân Trường',
          latitude: 11.88,
          longitude: 108.55,
          opening_hours: null,
          ticket_price: null,
          services: [],
          description: null,
          rating_avg: 0,
          primary_image_url: null,
        },
      ],
      page: 1,
      page_size: 3,
      total: 9,
    })
    const wrapper = mount(TourismSection, { global: { stubs } })
    await flushPromises()

    expect(getLocations).toHaveBeenCalledWith({ page: 1, page_size: 3, sort: 'rating' })
    expect(wrapper.findAllComponents({ name: 'LocationCard' })).toHaveLength(1)
    expect(wrapper.text()).not.toContain('Dữ liệu minh họa')
  })

  it('cho phep thu lai khi api loi', async () => {
    vi.mocked(getLocations).mockRejectedValueOnce(new Error('network'))
    const wrapper = mount(TourismSection, { global: { stubs } })
    await flushPromises()
    expect(wrapper.text()).toContain('Chưa tải được danh sách điểm du lịch.')

    vi.mocked(getLocations).mockResolvedValueOnce({ items: [], page: 1, page_size: 3, total: 0 })
    await wrapper.get('button').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Chưa có điểm du lịch nào được công bố.')
  })
})
