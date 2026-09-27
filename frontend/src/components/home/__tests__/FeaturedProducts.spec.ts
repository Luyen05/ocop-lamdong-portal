// @vitest-environment jsdom
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import FeaturedProducts from '@/components/home/FeaturedProducts.vue'
import { getProducts } from '@/services/products'
import type { ProductListItem } from '@/types/product'

enableAutoUnmount(afterEach)

vi.mock('@/services/products', () => ({
  getProducts: vi.fn(),
}))

function product(id: number, star: number): ProductListItem {
  return {
    id,
    name: `Sản phẩm ${id}`,
    slug: `san-pham-${id}`,
    star,
    price: 100000,
    unit: 'hộp',
    description: 'Mô tả',
    rating_avg: 4.5,
    vietgap_code: null,
    primary_image_url: null,
    category: { id: 1, name: 'Thực phẩm', slug: 'thuc-pham' },
    subject: { id: 1, name: 'Chủ thể', district: 'Đà Lạt' },
    created_at: '2026-01-01T00:00:00Z',
  }
}

describe('FeaturedProducts', () => {
  it('uu tien san pham bon den nam sao va gioi han tam the', async () => {
    const items = [product(1, 3), ...Array.from({ length: 9 }, (_, index) => product(index + 2, index % 2 ? 4 : 5))]
    vi.mocked(getProducts).mockResolvedValue({ items, page: 1, page_size: 8, total: items.length })

    const wrapper = mount(FeaturedProducts, {
      global: {
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
          ProductCard: { props: ['product'], template: '<div class="stub-card">{{ product.name }}-{{ product.star }}</div>' },
        },
      },
    })
    await flushPromises()

    const cards = wrapper.findAll('.stub-card')
    expect(cards).toHaveLength(8)
    expect(cards.every((card) => !card.text().endsWith('-3'))).toBe(true)
    expect(getProducts).toHaveBeenCalledWith({ page: 1, page_size: 100, sort: 'rating' })
  })
})

describe('FeaturedProducts certification filter', () => {
  it.each([
    { stars: [3, 3], expectedNames: [] },
    { stars: [3, 4, 3, 5], expectedNames: [product(2, 4).name, product(4, 5).name] },
    { stars: [], expectedNames: [] },
  ])('shows only certified cards for $stars', async ({ stars, expectedNames }) => {
    const items = stars.map((star, index) => product(index + 1, star))
    vi.mocked(getProducts).mockResolvedValue({ items, page: 1, page_size: 8, total: items.length })
    const wrapper = mount(FeaturedProducts, {
      global: {
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
          ProductCard: { props: ['product'], template: '<div class="stub-card">{{ product.name }}</div>' },
        },
      },
    })
    await flushPromises()

    expect(wrapper.findAll('.stub-card').map((card) => card.text())).toEqual(expectedNames)
    expect(wrapper.find('.featured-empty').exists()).toBe(expectedNames.length === 0)
    if (expectedNames.length === 0) {
      expect(wrapper.get('[role="status"]').text()).toContain('Chưa có sản phẩm nổi bật.')
      expect(wrapper.find('button').exists()).toBe(false)
    }
    wrapper.unmount()
  })
})
