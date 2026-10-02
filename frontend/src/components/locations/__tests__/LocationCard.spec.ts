// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import { flowerFarmPhoto, heroPhoto, teaPhoto } from '@/constants/photos'
import type { LocationListItem } from '@/types/location'

import LocationCard from '../LocationCard.vue'

function build(overrides: Partial<LocationListItem> = {}): LocationListItem {
  return {
    id: 1,
    name: 'Đồi chè Cầu Đất',
    slug: 'doi-che-cau-dat',
    type: 'tea_coffee_farm',
    type_label: 'Đồi chè & cà phê',
    district: 'Đà Lạt',
    address: 'Cầu Đất, Đà Lạt',
    latitude: 11.9,
    longitude: 108.5,
    opening_hours: '07:00 - 17:00',
    ticket_price: 30000,
    services: ['Tham quan'],
    description: 'Đồi chè',
    primary_image_url: null,
    ...overrides,
  } as LocationListItem
}

const stubs = { RouterLink: { template: '<a><slot /></a>' } }

describe('LocationCard', () => {
  it('chưa có ảnh riêng thì dùng ảnh cảnh quan thật theo loại hình', () => {
    const wrapper = mount(LocationCard, { props: { location: build() }, global: { stubs } })
    const image = wrapper.get('img')
    expect(image.attributes('src')).toBe(teaPhoto.src)
    expect(image.attributes('alt')).toBe('')
  })

  it('loại hình khác dùng ảnh tương ứng, loại lạ dùng ảnh mặc định', () => {
    const vegetable = mount(LocationCard, { props: { location: build({ type: 'vegetable_farm' }) }, global: { stubs } })
    expect(vegetable.get('img').attributes('src')).toBe(flowerFarmPhoto.src)
    const unknown = mount(LocationCard, { props: { location: build({ type: 'other' as never }) }, global: { stubs } })
    expect(unknown.get('img').attributes('src')).toBe(heroPhoto.src)
  })

  it('có ảnh riêng thì dùng ảnh đó và đặt alt theo tên điểm', () => {
    const wrapper = mount(LocationCard, {
      props: { location: build({ primary_image_url: '/uploads/a.jpg' }) },
      global: { stubs },
    })
    expect(wrapper.get('img').attributes('src')).toBe('/uploads/a.jpg')
    expect(wrapper.get('img').attributes('alt')).toBe('Đồi chè Cầu Đất')
  })

  it('ảnh riêng lỗi thì chuyển sang ảnh dự phòng', async () => {
    const wrapper = mount(LocationCard, {
      props: { location: build({ primary_image_url: '/uploads/hong.jpg' }) },
      global: { stubs },
    })
    await wrapper.get('img').trigger('error')
    expect(wrapper.get('img').attributes('src')).toBe(teaPhoto.src)
  })
})
