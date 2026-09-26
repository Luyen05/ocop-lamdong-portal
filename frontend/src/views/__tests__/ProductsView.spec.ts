// @vitest-environment jsdom
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { reactive } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

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

enableAutoUnmount(afterEach)

describe('ProductsView', () => {
  beforeEach(() => {
    route.query = {}
    vi.resetAllMocks()
    const navigate = async (target: { query?: Record<string, string> }) => {
      route.query = { ...target.query }
    }
    router.push.mockImplementation(navigate)
    router.replace.mockImplementation(navigate)
    vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
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
  it('keeps draft search out of chips, URL and requests until submit', async () => {
    const wrapper = mount(ProductsView)
    await flushPromises()
    await wrapper.get('#product-search').setValue('atiso')

    expect(route.query).toEqual({})
    expect(router.push).not.toHaveBeenCalled()
    expect(wrapper.find('.active-filters').exists()).toBe(false)
    expect(getProducts).toHaveBeenCalledTimes(1)
  })

  it('paginates with applied filters instead of draft values', async () => {
    route.query = { search: 'coffee', category: 'do-uong' }
    const wrapper = mount(ProductsView)
    await flushPromises()
    await wrapper.get('#product-search').setValue('atiso')
    await wrapper.get('.page-number:nth-child(2)').trigger('click')
    await flushPromises()

    expect(route.query).toEqual({ search: 'coffee', category: 'do-uong', page: '2' })
    expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({
      search: 'coffee', category: 'do-uong', page: 2,
    }))
    expect(wrapper.get('.active-filters').text()).toContain('coffee')
    expect(wrapper.get('.active-filters').text()).not.toContain('atiso')
  })

  it('retries the applied query after an error despite draft edits', async () => {
    route.query = { search: 'coffee' }
    vi.mocked(getProducts).mockRejectedValueOnce(new Error('Network error'))
    const wrapper = mount(ProductsView)
    await flushPromises()
    await wrapper.get('#product-search').setValue('atiso')
    await wrapper.get('.alert-danger button').trigger('click')
    await flushPromises()

    expect(getProducts).toHaveBeenCalledTimes(2)
    expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({ search: 'coffee' }))
    expect(route.query).toEqual({ search: 'coffee' })
    expect(wrapper.find('.alert-danger').exists()).toBe(false)
  })

  it('submits draft filters through the URL and resets the page', async () => {
    route.query = { search: 'coffee', page: '3' }
    const wrapper = mount(ProductsView)
    await flushPromises()
    await wrapper.get('#product-search').setValue('atiso')
    await wrapper.get('#product-star').setValue('3')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(route.query).toEqual({ search: 'atiso', star: '3' })
    expect(getProducts).toHaveBeenCalledTimes(2)
    expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({
      search: 'atiso', star: 3, page: 1,
    }))
    expect(wrapper.get('.active-filters').text()).toContain('atiso')
  })

  it('hydrates form, chips and requests on back/forward query changes', async () => {
    route.query = { search: 'coffee', star: '4' }
    const wrapper = mount(ProductsView)
    await flushPromises()
    await wrapper.get('#product-search').setValue('unsubmitted')
    route.query = { search: 'atiso', star: '3', page: '2' }
    await flushPromises()

    expect((wrapper.get('#product-search').element as HTMLInputElement).value).toBe('atiso')
    expect((wrapper.get('#product-star').element as HTMLSelectElement).value).toBe('3')
    expect(wrapper.get('.active-filters').text()).toContain('atiso')
    expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({ search: 'atiso', star: 3, page: 2 }))

    route.query = { search: 'coffee', star: '4' }
    await flushPromises()
    expect((wrapper.get('#product-search').element as HTMLInputElement).value).toBe('coffee')
    expect(wrapper.get('.active-filters').text()).not.toContain('atiso')
    expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({ search: 'coffee', star: 4, page: 1 }))
  })

  it('removes an applied chip without applying other draft edits', async () => {
    route.query = { search: 'coffee', star: '4', page: '2', sort: 'name' }
    const wrapper = mount(ProductsView)
    await flushPromises()
    await wrapper.get('#product-search').setValue('atiso')
    await wrapper.get('#product-star').setValue('3')
    await wrapper.get('.active-filters button').trigger('click')
    await flushPromises()

    expect(route.query).toEqual({ star: '4', sort: 'name' })
    expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({
      search: undefined, star: 4, sort: 'name', page: 1,
    }))
  })

  it('clears all applied filters and hydrates the empty form', async () => {
    route.query = { search: 'coffee', star: '4', page: '2' }
    const wrapper = mount(ProductsView)
    await flushPromises()
    await wrapper.get('#product-search').setValue('atiso')
    await wrapper.get('.btn-reset').trigger('click')
    await flushPromises()

    expect(route.query).toEqual({})
    expect((wrapper.get('#product-search').element as HTMLInputElement).value).toBe('')
    expect(wrapper.find('.active-filters').exists()).toBe(false)
    expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({ search: undefined, star: undefined, page: 1 }))
  })

  it('corrects an out-of-range page using applied filters', async () => {
    route.query = { search: 'coffee', page: '99' }
    let resolveRequest!: (value: Awaited<ReturnType<typeof getProducts>>) => void
    vi.mocked(getProducts).mockReturnValueOnce(new Promise((resolve) => { resolveRequest = resolve }))
    const wrapper = mount(ProductsView)
    await wrapper.get('#product-search').setValue('atiso')
    resolveRequest({ items: [], page: 99, page_size: 12, total: 62 })
    await flushPromises()

    expect(router.replace).toHaveBeenCalledWith({ name: 'products', query: { search: 'coffee', page: '6' } })
    expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({ search: 'coffee', page: 6 }))
  })

})
