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

  function pointAt(slug: string, name: string, coordinates: unknown): MapFeature {
    return {
      ...features[0],
      geometry: { type: 'Point', coordinates } as MapFeature['geometry'],
      properties: { ...features[0].properties, slug, name },
    }
  }

  const press = (element: Element, key: string) => {
    const event = new KeyboardEvent('keypress', { key, bubbles: true, cancelable: true })
    element.dispatchEvent(event)
    return event
  }

  it('Enter va Space tren marker chon diem, phim khac thi khong, marker co nhan doc duoc', async () => {
    const wrapper = mount(LeafletMap, { attachTo: document.body, props: { features, cluster: false } })
    await flushPromises()
    const marker = wrapper.get('.leaflet-marker-icon').element

    expect(marker.getAttribute('aria-label')).toBe('<img src=x onerror=alert(1)>, Đồi chè & cà phê')
    expect(marker.getAttribute('title')).toContain('Đồi chè & cà phê')
    expect(marker.getAttribute('role')).toBe('button')
    expect(marker.getAttribute('tabindex')).toBe('0')

    press(marker, 'a')
    expect(wrapper.emitted('select')).toBeUndefined()
    expect(press(marker, 'Enter').defaultPrevented).toBe(true)
    expect(press(marker, ' ').defaultPrevented).toBe(true)
    expect(wrapper.emitted('select')).toEqual([['cau-dat-farm'], ['cau-dat-farm']])
    wrapper.unmount()
  })

  it('bo qua diem toa do null, [0,0] hoac ngoai Lam Dong ma khong lam hong marker con lai', async () => {
    const mixed = [
      pointAt('ok', 'Điểm tốt', [108.45, 11.94]),
      pointAt('null', 'Null', null),
      pointAt('zero', 'Zero', [0, 0]),
      pointAt('far', 'Hà Nội', [105.85, 21.03]),
      pointAt('nan', 'NaN', [Number.NaN, Number.NaN]),
    ]
    const wrapper = mount(LeafletMap, { attachTo: document.body, props: { features: mixed, cluster: false } })
    await flushPromises()
    expect(wrapper.findAll('.leaflet-marker-icon')).toHaveLength(1)
    expect(wrapper.find('.map-load-error').exists()).toBe(false)

    // Chon diem khong co marker: khong loi, khong phat su kien
    await wrapper.setProps({ selectedSlug: 'zero' })
    await wrapper.setProps({ selectedSlug: 'ok' })
    expect(wrapper.find('.map-load-error').exists()).toBe(false)
    wrapper.unmount()
  })

  it('doi diem chon chi doi class, giu nguyen phan tu marker (khong mat focus ban phim)', async () => {
    const two = [pointAt('a', 'A', [108.45, 11.94]), pointAt('b', 'B', [108.5, 11.95])]
    const wrapper = mount(LeafletMap, { attachTo: document.body, props: { features: two, cluster: false } })
    await flushPromises()
    const before = wrapper.findAll('.leaflet-marker-icon').map((item) => item.element)

    await wrapper.setProps({ selectedSlug: 'a' })
    expect(wrapper.findAll('.ocop-marker.is-selected')).toHaveLength(1)
    await wrapper.setProps({ selectedSlug: 'b' })
    const after = wrapper.findAll('.leaflet-marker-icon').map((item) => item.element)
    expect(after).toEqual(before)
    const selected = wrapper.findAll('.ocop-marker.is-selected')
    expect(selected).toHaveLength(1)
    expect(selected[0].element.closest('.leaflet-marker-icon')).toBe(after.find((item) => item.getAttribute('aria-label')?.startsWith('B,')))
    wrapper.unmount()
  })
})
