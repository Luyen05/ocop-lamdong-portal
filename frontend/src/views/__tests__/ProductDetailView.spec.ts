// @vitest-environment jsdom
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { reactive } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import ProductDetailView from '@/views/ProductDetailView.vue'
import { getProduct, getProducts } from '@/services/products'
import type { ProductDetail, ProductListItem } from '@/types/product'

enableAutoUnmount(afterEach)

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

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason: unknown) => void
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

function mountDetail() {
  return mount(ProductDetailView, {
    global: {
      stubs: {
        RouterLink: { props: ['to'], template: '<a><slot /></a>' },
        ProductCard: { props: ['product'], template: '<div class="related-card">{{ product.name }}</div>' },
      },
    },
  })
}

describe('ProductDetailView overlapping requests', () => {
  const productB = { ...product, id: 3, slug: 'product-b', name: 'Product B' }
  const relatedB = { ...relatedProduct, id: 4, name: 'Related B' }
  const relatedResponse = {
    items: [relatedB], page: 1, page_size: 4, total: 1,
  }

  beforeEach(() => {
    vi.resetAllMocks()
    route.params.slug = product.slug
    vi.mocked(getProducts).mockResolvedValue(relatedResponse)
  })

  it('keeps B when product A resolves after B', async () => {
    const requestA = deferred<ProductDetail>()
    const requestB = deferred<ProductDetail>()
    vi.mocked(getProduct)
      .mockReturnValueOnce(requestA.promise)
      .mockReturnValueOnce(requestB.promise)
    const wrapper = mountDetail()
    route.params.slug = productB.slug
    await flushPromises()
    expect(getProduct).toHaveBeenNthCalledWith(2, productB.slug)

    requestB.resolve(productB)
    await flushPromises()
    expect(wrapper.get('h1').text()).toBe(productB.name)
    requestA.resolve(product)
    await flushPromises()

    expect(wrapper.get('h1').text()).toBe(productB.name)
    expect(document.title).toContain(productB.name)
    expect(wrapper.get('.related-card').text()).toBe(relatedB.name)
    expect(getProducts).toHaveBeenCalledTimes(1)
  })

  it.each(['pending', 'resolved'] as const)(
    'ignores stale product errors while B is %s', async (state) => {
      const requestA = deferred<ProductDetail>()
      const requestB = deferred<ProductDetail>()
      vi.mocked(getProduct)
        .mockReturnValueOnce(requestA.promise)
        .mockReturnValueOnce(requestB.promise)
      const wrapper = mountDetail()
      route.params.slug = productB.slug
      await flushPromises()
      if (state === 'resolved') {
        requestB.resolve(productB)
        await flushPromises()
      }
      requestA.reject(new Error('Stale A error'))
      await flushPromises()

      expect(wrapper.find('.error-state').exists()).toBe(false)
      expect(wrapper.find('.detail-loading').exists()).toBe(state === 'pending')
      if (state === 'pending') {
        requestB.resolve(productB)
        await flushPromises()
      }
      expect(wrapper.get('h1').text()).toBe(productB.name)
    },
  )

  it.each(['resolve', 'reject'] as const)(
    'ignores stale related products that %s after B', async (outcome) => {
      const relatedA = deferred<Awaited<ReturnType<typeof getProducts>>>()
      vi.mocked(getProduct).mockResolvedValueOnce(product).mockResolvedValueOnce(productB)
      vi.mocked(getProducts).mockReturnValueOnce(relatedA.promise)
      const wrapper = mountDetail()
      await flushPromises()
      route.params.slug = productB.slug
      await flushPromises()
      expect(wrapper.get('.related-card').text()).toBe(relatedB.name)

      if (outcome === 'resolve') {
        relatedA.resolve({ ...relatedResponse, items: [relatedProduct] })
      } else {
        relatedA.reject(new Error('Stale related error'))
      }
      await flushPromises()
      expect(wrapper.get('h1').text()).toBe(productB.name)
      expect(wrapper.get('.related-card').text()).toBe(relatedB.name)
    },
  )

  it('keeps loading B when stale related products finish', async () => {
    const relatedA = deferred<Awaited<ReturnType<typeof getProducts>>>()
    const requestB = deferred<ProductDetail>()
    vi.mocked(getProduct).mockResolvedValueOnce(product).mockReturnValueOnce(requestB.promise)
    vi.mocked(getProducts).mockReturnValueOnce(relatedA.promise)
    const wrapper = mountDetail()
    await flushPromises()
    route.params.slug = productB.slug
    await flushPromises()
    relatedA.resolve({ ...relatedResponse, items: [relatedProduct] })
    await flushPromises()
    expect(wrapper.find('.detail-loading').exists()).toBe(true)

    requestB.resolve(productB)
    await flushPromises()
    expect(wrapper.get('h1').text()).toBe(productB.name)
    expect(wrapper.get('.related-card').text()).toBe(relatedB.name)
  })
})
