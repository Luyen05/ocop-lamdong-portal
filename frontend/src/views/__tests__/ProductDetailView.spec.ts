// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { reactive } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ProductDetailView from '@/views/ProductDetailView.vue'
import { getProduct, getProducts } from '@/services/products'
import type { ProductDetail, ProductListItem } from '@/types/product'

const route = reactive({ params: { slug: 'tra-atiso-da-lat' } })

vi.mock('vue-router', () => ({
  useRoute: () => route,
}))

vi.mock('@/services/products', () => ({
  getProduct: vi.fn(),
  getProducts: vi.fn(),
}))

const relatedProduct: ProductListItem = {
  id: 2,
  name: 'Cao atiso Lâm Đồng',
  slug: 'cao-atiso-lam-dong',
  star: 3,
  price: null,
  unit: null,
  description: 'Sản phẩm cùng danh mục.',
  rating_avg: 0,
  vietgap_code: null,
  primary_image_url: null,
  category: { id: 1, name: 'Thảo dược', slug: 'thao-duoc' },
  subject: { id: 2, name: 'Cơ sở Hoàng An', district: 'xã Lạc Dương' },
  created_at: '2026-09-13T00:00:00Z',
}

const product: ProductDetail = {
  ...relatedProduct,
  id: 1,
  name: 'Trà atiso Đà Lạt',
  slug: 'tra-atiso-da-lat',
  primary_image_url: 'https://example.com/tra-atiso.jpg',
  cert_code: '3981/QĐ-UBND',
  cert_year: 2026,
  cert_issued_at: '2026-08-05',
  cert_expires_at: '2029-08-05',
  issuing_authority: 'Ủy ban nhân dân tỉnh Lâm Đồng',
  story: 'Câu chuyện sản phẩm.',
  ingredients: 'Atiso.',
  usage_instructions: 'Pha với nước nóng.',
  views: 0,
  images: [
    {
      id: 1,
      image_url: 'https://example.com/tra-atiso.jpg',
      is_primary: true,
      sort_order: 0,
    },
  ],
  recognition_sources: [
    {
      id: 1,
      title: 'Quyết định công nhận sản phẩm OCOP năm 2026',
      document_number: '3981/QĐ-UBND',
      issuing_body: 'UBND tỉnh Lâm Đồng',
      published_at: '2026-08-05',
      source_url: 'https://example.com/quyet-dinh-3981',
      verification_level: 'A',
    },
  ],
  updated_at: '2026-09-13T00:00:00Z',
}

describe('ProductDetailView', () => {
  beforeEach(() => {
    route.params.slug = 'tra-atiso-da-lat'
    vi.clearAllMocks()
    vi.mocked(getProduct).mockResolvedValue(product)
    vi.mocked(getProducts).mockResolvedValue({
      items: [product, relatedProduct],
      page: 1,
      page_size: 4,
      total: 2,
    })
  })

  it('hien thi chung nhan nguon cong khai va san pham lien quan', async () => {
    const wrapper = mount(ProductDetailView, {
      global: {
        stubs: {
          RouterLink: { props: ['to'], template: '<a><slot /></a>' },
          ProductCard: { props: ['product'], template: '<div class="related-card">{{ product.name }}</div>' },
        },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('3981/QĐ-UBND')
    expect(wrapper.text()).toContain('Quyết định công nhận sản phẩm OCOP năm 2026')
    expect(wrapper.get('.source-block a').attributes('rel')).toBe('noopener noreferrer')
    expect(wrapper.findAll('.related-card')).toHaveLength(1)

    await wrapper.get('.main-image img').trigger('error')
    expect(wrapper.find('.main-image .image-placeholder').exists()).toBe(true)
    wrapper.unmount()
  })
})
