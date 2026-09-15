// @vitest-environment jsdom
import { AxiosError, AxiosHeaders } from 'axios'
import { flushPromises, mount } from '@vue/test-utils'
import { reactive } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getProduct } from '@/services/products'
import type { ProductDetail } from '@/types/product'
import ProductDetailView from '@/views/ProductDetailView.vue'

const route = reactive({ params: { slug: 'first-product' } })

vi.mock('vue-router', () => ({ useRoute: () => route }))
vi.mock('@/services/products', () => ({ getProduct: vi.fn() }))

const product: ProductDetail = {
  id: 1, name: 'Cà phê Đà Lạt', slug: 'first-product', star: 4,
  price: 100000, unit: 'hộp', description: 'Cà phê ngon', rating_avg: 4.5,
  primary_image_url: null, category: { id: 1, name: 'Đồ uống', slug: 'do-uong' },
  subject: { id: 1, name: 'Nhà sản xuất', district: 'Đà Lạt' },
  created_at: '2026-01-01', cert_code: null, cert_year: null,
  vietgap_code: null, story: null, ingredients: null, usage_instructions: null,
  views: 10, images: [], updated_at: '2026-01-01',
}

function mountView() {
  return mount(ProductDetailView, {
    global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
  })
}

function httpError(status: number, message?: string) {
  return new AxiosError('Request failed', 'ERR_BAD_RESPONSE', undefined, undefined, {
    status, statusText: '', headers: {}, config: { headers: new AxiosHeaders() },
    data: message ? { message } : {},
  })
}

describe('ProductDetailView', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    route.params.slug = 'first-product'
  })

  it('shows the backend message for a 404', async () => {
    vi.mocked(getProduct).mockRejectedValue(httpError(404, 'Không tìm thấy sản phẩm.'))
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.get('.error-state h1').text()).toBe('Không tìm thấy sản phẩm')
    expect(wrapper.get('.error-state p').text()).toBe('Không tìm thấy sản phẩm.')
    expect(wrapper.text()).toContain('Quay lại danh sách')
  })

  it('shows a connection error and retries the current slug', async () => {
    vi.mocked(getProduct).mockRejectedValueOnce(new AxiosError('Network Error')).mockResolvedValue(product)
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.get('.error-state h1').text()).toBe('Không thể tải sản phẩm')
    expect(wrapper.get('.error-state p').text()).toContain('Không thể kết nối đến máy chủ')
    route.params.slug = 'second-product'
    await wrapper.get('.error-state button').trigger('click')
    await flushPromises()
    expect(getProduct).toHaveBeenLastCalledWith('second-product')
  })

  it('shows a loading error for a 500 response', async () => {
    vi.mocked(getProduct).mockRejectedValue(httpError(500, 'Máy chủ gặp lỗi.'))
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.get('.error-state h1').text()).toBe('Không thể tải sản phẩm')
    expect(wrapper.get('.error-state p').text()).toBe('Máy chủ gặp lỗi.')
    expect(wrapper.get('.error-state button').text()).toBe('Thử lại')
  })

  it('renders a successfully loaded product', async () => {
    vi.mocked(getProduct).mockResolvedValue(product)
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.get('.product-info h1').text()).toBe(product.name)
    expect(wrapper.find('.error-state').exists()).toBe(false)
  })
})
