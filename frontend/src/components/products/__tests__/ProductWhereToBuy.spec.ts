// @vitest-environment jsdom
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import ProductWhereToBuy from '@/components/products/ProductWhereToBuy.vue'
import { getProductLocations } from '@/services/locations'
import type { ProductLocationItem } from '@/types/location'

enableAutoUnmount(afterEach)

vi.mock('@/services/locations', () => ({
  getProductLocations: vi.fn(),
}))

const LeafletMapStub = defineComponent({
  name: 'LeafletMap',
  props: ['features', 'links', 'cluster', 'initialZoom', 'label'],
  template: '<div class="map-stub" />',
})
const RouterLinkStub = defineComponent({
  props: ['to'],
  template: '<a :data-to="JSON.stringify(to)"><slot /></a>',
})

function place(overrides: Partial<ProductLocationItem>): ProductLocationItem {
  return {
    id: 1,
    name: 'Cửa hàng DaLaVi - 27/6E Yersin',
    slug: 'dalavi-cua-hang-yersin',
    type: 'ocop_store',
    type_label: 'Cửa hàng OCOP',
    kind: 'shop',
    district: 'Đà Lạt',
    address: '27/6E Yersin, Đà Lạt',
    latitude: 11.943,
    longitude: 108.4494,
    opening_hours: null,
    ticket_price: null,
    services: [],
    description: null,
    rating_avg: 0,
    primary_image_url: null,
    role: 'sold_here',
    ...overrides,
  }
}

const items = [
  place({}),
  place({
    id: 2,
    name: 'Cơ sở DaLaVi - Păng Tiêng',
    slug: 'dalavi-co-so-pang-tieng',
    type: 'workshop',
    type_label: 'Cơ sở sản xuất',
    latitude: 11.99,
    longitude: 108.347,
    role: 'produced_here',
  }),
]

const mountSection = () =>
  mount(ProductWhereToBuy, {
    props: { slug: 'dau-tay-say-deo-dalavi', subject: { id: 9, name: 'Công ty TNHH DaLaVi' } },
    global: { stubs: { RouterLink: RouterLinkStub, LeafletMap: LeafletMapStub } },
  })

describe('ProductWhereToBuy', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('liet ke noi ban va noi san xuat kem vai tro, noi hai diem tren ban do nho', async () => {
    vi.mocked(getProductLocations).mockResolvedValue({
      product_id: 1,
      product_name: 'Dâu tây sấy dẻo',
      product_slug: 'dau-tay-say-deo-dalavi',
      items,
    })
    const wrapper = mountSection()
    await flushPromises()

    expect(getProductLocations).toHaveBeenCalledWith('dau-tay-say-deo-dalavi')
    const places = wrapper.findAll('[data-test="where-place"]')
    expect(places).toHaveLength(2)
    expect(places[0]!.text()).toContain('Cửa hàng DaLaVi - 27/6E Yersin')
    expect(places[0]!.get('[data-test="where-role"]').text()).toBe('Bán tại đây')
    expect(places[1]!.get('[data-test="where-role"]').text()).toBe('Sản xuất tại đây')

    const map = wrapper.getComponent(LeafletMapStub)
    expect(map.props('features')).toHaveLength(2)
    expect(map.props('links')).toEqual([['dalavi-co-so-pang-tieng', 'dalavi-cua-hang-yersin']])
    expect(map.props('cluster')).toBe(true)
  })

  it('co lien ket sang ban do lon theo san pham, theo chu the va chi duong tung diem', async () => {
    vi.mocked(getProductLocations).mockResolvedValue({
      product_id: 1,
      product_name: 'Dâu tây sấy dẻo',
      product_slug: 'dau-tay-say-deo-dalavi',
      items,
    })
    const wrapper = mountSection()
    await flushPromises()

    expect(wrapper.get('[data-test="where-map-link"]').attributes('data-to')).toBe(
      JSON.stringify({ name: 'map', query: { product: 'dau-tay-say-deo-dalavi' } }),
    )
    expect(wrapper.get('[data-test="where-subject-link"]').attributes('data-to')).toBe(
      JSON.stringify({ name: 'map', query: { subject: '9' } }),
    )
    const route = wrapper.findAll('[data-test="where-place"] a')[0]!
    expect(route.attributes('data-to')).toBe(
      JSON.stringify({ name: 'map', query: { diem: 'dalavi-cua-hang-yersin', action: 'route' } }),
    )
  })

  it('khong hien khoi nay khi san pham chua co diem ban nao', async () => {
    vi.mocked(getProductLocations).mockResolvedValue({
      product_id: 1,
      product_name: 'Dâu tây sấy dẻo',
      product_slug: 'dau-tay-say-deo-dalavi',
      items: [],
    })
    const wrapper = mountSection()
    await flushPromises()

    expect(wrapper.find('[data-test="where-to-buy"]').exists()).toBe(false)
  })

  it('bao loi va cho thu lai', async () => {
    vi.mocked(getProductLocations).mockRejectedValueOnce(new Error('network'))
    const wrapper = mountSection()
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toContain('Thử lại')

    vi.mocked(getProductLocations).mockResolvedValueOnce({
      product_id: 1,
      product_name: 'Dâu tây sấy dẻo',
      product_slug: 'dau-tay-say-deo-dalavi',
      items,
    })
    await wrapper.get('.where-retry').trigger('click')
    await flushPromises()

    expect(wrapper.findAll('[data-test="where-place"]')).toHaveLength(2)
  })
})
