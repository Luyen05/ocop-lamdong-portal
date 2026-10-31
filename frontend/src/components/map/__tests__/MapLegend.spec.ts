// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import MapLegend from '@/components/map/MapLegend.vue'
import type { LocationType, MapFeature } from '@/types/location'

function point(slug: string, type: LocationType, label: string): MapFeature {
  return {
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [108.45, 11.94] },
    properties: {
      id: 1, slug, name: slug, type, type_label: label, district: 'Đà Lạt', address: 'x',
      opening_hours: null, ticket_price: null, rating_avg: 0, primary_image_url: null,
    },
  }
}

const features = [
  point('a', 'fruit_garden', 'Vườn trái cây'),
  point('b', 'fruit_garden', 'Vườn trái cây'),
  point('c', 'dairy_farm', 'Trang trại bò sữa'),
]

describe('MapLegend', () => {
  it('chi liet ke loai hinh co that, kem so diem, icon va chu', () => {
    const wrapper = mount(MapLegend, { props: { features, activeType: '' } })
    const items = wrapper.findAll('button.legend-item')
    expect(items).toHaveLength(2)
    expect(items[0].text()).toContain('Vườn trái cây')
    expect(items[0].text()).toContain('2')
    expect(items[0].get('.legend-count').text()).toContain('điểm') // chữ cho trình đọc màn hình
    expect(items[0].find('i.bi-basket-fill').exists()).toBe(true)
    expect(items[1].find('i.bi-house-heart-fill').exists()).toBe(true)
    expect(items[0].get('.legend-swatch').attributes('style')).toContain('--ocop-location-fruit')
  })

  it('aria-pressed phan anh loai dang loc, bam de loc va bam lai de bo loc', async () => {
    const wrapper = mount(MapLegend, { props: { features, activeType: 'dairy_farm' } })
    const [fruit, dairy] = wrapper.findAll('button.legend-item')
    expect(fruit.attributes('aria-pressed')).toBe('false')
    expect(dairy.attributes('aria-pressed')).toBe('true')

    await fruit.trigger('click')
    await dairy.trigger('click')
    expect(wrapper.emitted('select')).toEqual([['fruit_garden'], ['']])
  })

  it('khong hien gi khi khong co diem', () => {
    const wrapper = mount(MapLegend, { props: { features: [], activeType: '' } })
    expect(wrapper.find('.map-legend').exists()).toBe(false)
  })
})
