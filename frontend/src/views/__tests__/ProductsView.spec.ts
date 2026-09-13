// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { reactive } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ProductsView from '@/views/ProductsView.vue'
import { getCategories } from '@/services/categories'
import { getProductFilterOptions, getProducts } from '@/services/products'

const route = reactive({ query: {} as Record<string, string> })
const router = {
  push: vi.fn().mockResolvedValue(undefined),
  replace: vi.fn().mockResolvedValue(undefined),
}

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => router,
}))

vi.mock('@/services/products', () => ({
  getProducts: vi.fn(),
  getProductFilterOptions: vi.fn(),
}))

vi.mock('@/services/categories', () => ({
  getCategories: vi.fn(),
}))

describe('ProductsView', () => {
  beforeEach(() => {
    route.query = {}
    vi.clearAllMocks()
    vi.mocked(getProducts).mockResolvedValue({ items: [], page: 1, page_size: 12, total: 62 })
    vi.mocked(getProductFilterOptions).mockResolvedValue({ districts: ['phường Đà Lạt', 'xã Tánh Linh'] })
    vi.mocked(getCategories).mockResolvedValue({ items: [], page: 1, page_size: 100, total: 0 })
  })

  it('tai goi y dia ban va hien thi phan trang co so', async () => {
    const wrapper = mount(ProductsView, {
      global: {
        stubs: {
          ProductCard: true,
        },
      },
    })
    await flushPromises()

    expect(wrapper.findAll('#product-district-options option')).toHaveLength(2)
    expect(wrapper.findAll('.page-number')).toHaveLength(5)
    expect(wrapper.text()).toContain('62 sản phẩm phù hợp')
  })

  it('chan khoang gia khong hop le truoc khi goi api', async () => {
    const wrapper = mount(ProductsView)
    await flushPromises()
    vi.mocked(router.push).mockClear()

    await wrapper.get('[aria-label="Giá tối thiểu"]').setValue('200000')
    await wrapper.get('[aria-label="Giá tối đa"]').setValue('100000')
    await wrapper.get('form').trigger('submit')

    expect(wrapper.text()).toContain('Giá tối thiểu không được lớn hơn giá tối đa.')
    expect(router.push).not.toHaveBeenCalled()
  })
})
