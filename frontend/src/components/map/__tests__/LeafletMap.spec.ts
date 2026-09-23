// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import LeafletMap from '@/components/map/LeafletMap.vue'
import type { MapFeature } from '@/types/location'

const features: MapFeature[] = [
  {
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [108.547398, 11.879583] },
    properties: {
      id: 1,
      slug: 'cau-dat-farm',
      name: '<img src=x onerror=alert(1)>',
      type: 'tea_coffee_farm',
      type_label: 'Đồi chè & cà phê',
      district: 'Đà Lạt',
      address: 'Xuân Trường',
      opening_hours: null,
      ticket_price: null,
      rating_avg: 0,
      primary_image_url: null,
    },
  },
]

describe('LeafletMap', () => {
  it('ve marker theo loai hinh, phat su kien chon va khong chen html tu du lieu', async () => {
    const wrapper = mount(LeafletMap, {
      attachTo: document.body,
      props: { features, cluster: false },
    })
    await flushPromises()

    const marker = wrapper.find('.leaflet-marker-icon')
    expect(marker.exists()).toBe(true)
    expect(marker.find('.bi-cup-hot-fill').exists()).toBe(true)
    expect(document.body.querySelector('img[src="x"]')).toBeNull()

    await marker.trigger('click')
    expect(wrapper.emitted('select')?.[0]).toEqual(['cau-dat-farm'])

    await wrapper.setProps({ route: [[108.4383, 11.9404], [108.547398, 11.879583]] })
    expect(wrapper.find('path.leaflet-interactive').exists()).toBe(true)
    wrapper.unmount()
  })
})
