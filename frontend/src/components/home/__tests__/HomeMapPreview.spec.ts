// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import HomeMapPreview from '@/components/home/HomeMapPreview.vue'
import { getMapLocations } from '@/services/locations'
import type { MapFeature } from '@/types/location'

vi.mock('@/services/locations', () => ({
  getMapLocations: vi.fn(),
}))

function feature(slug: string, type: MapFeature['properties']['type'], coordinates: [number, number]): MapFeature {
  return {
    type: 'Feature',
    geometry: { type: 'Point', coordinates },
    properties: {
      id: slug.length,
      slug,
      name: slug,
      type,
      type_label: type === 'fruit_garden' ? 'Vườn trái cây' : 'Đồi chè & cà phê',
      district: 'Đà Lạt',
      address: 'Đà Lạt',
      opening_hours: null,
      ticket_price: null,
      rating_avg: 0,
      primary_image_url: null,
    },
  }
}

describe('HomeMapPreview', () => {
  it('chieu diem that len khung xem truoc va lien ket den trang ban do', async () => {
    vi.mocked(getMapLocations).mockResolvedValue({
      type: 'FeatureCollection',
      features: [
        feature('tay-bac', 'tea_coffee_farm', [107.7, 12.1]),
        feature('dong-nam', 'fruit_garden', [108.6, 11.6]),
      ],
    })
    const wrapper = mount(HomeMapPreview, {
      global: { stubs: { RouterLink: { props: ['to'], template: '<a class="router-link" :data-to="JSON.stringify(to)"><slot /></a>' } } },
    })
    await flushPromises()

    const markers = wrapper.findAll('.map-marker')
    expect(markers).toHaveLength(2)
    expect(markers[0].attributes('style')).toContain('left: 8%')
    expect(markers[0].attributes('style')).toContain('top: 10%')
    expect(markers[1].attributes('style')).toContain('left: 92%')
    expect(markers[0].attributes('data-to')).toContain('tay-bac')
    expect(wrapper.findAll('.map-legend span')).toHaveLength(2)
    expect(wrapper.text()).toContain('2 điểm đến')
  })

  it('hien thi thong bao khi chua co diem', async () => {
    vi.mocked(getMapLocations).mockRejectedValue(new Error('network'))
    const wrapper = mount(HomeMapPreview, { global: { stubs: { RouterLink: true } } })
    await flushPromises()

    expect(wrapper.text()).toContain('Chưa có điểm đến được công bố.')
  })
})
