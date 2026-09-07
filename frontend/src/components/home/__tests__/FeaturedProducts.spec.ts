// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import FeaturedProducts from '@/components/home/FeaturedProducts.vue'
import { getProducts } from '@/services/products'
import type { ProductListItem } from '@/types/product'

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
    primary_image_url: null,
    category: { id: 1, name: 'Thực phẩm', slug: 'thuc-pham' },
    subject: { id: 1, name: 'Chủ thể', district: 'Đà Lạt' },
    created_at: '2026-01-01T00:00:00Z',
  }
}

describe('FeaturedProducts', () => {
  it('uu tien san pham bon den nam sao va gioi han bon the', async () => {
    const items = [product(1, 3), product(2, 5), product(3, 4), product(4, 5), product(5, 4), product(6, 5)]
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
    expect(cards).toHaveLength(4)
    expect(cards.every((card) => !card.text().endsWith('-3'))).toBe(true)
    expect(getProducts).toHaveBeenCalledWith({ page: 1, page_size: 8, sort: 'rating' })
  })
})
