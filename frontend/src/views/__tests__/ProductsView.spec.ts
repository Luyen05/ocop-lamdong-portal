// @vitest-environment jsdom
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { reactive } from 'vue'
import { AxiosError, AxiosHeaders } from 'axios'
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
    await wrapper.get('.state-box.is-error button').trigger('click')
    await flushPromises()

    expect(getProducts).toHaveBeenCalledTimes(2)
    expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({ search: 'coffee' }))
    expect(route.query).toEqual({ search: 'coffee' })
    expect(wrapper.find('.state-box.is-error').exists()).toBe(false)
  })

  it('submits draft filters through the URL and resets the page', async () => {
    route.query = { search: 'coffee', star: '4', page: '3' }
    const wrapper = mount(ProductsView)
    await flushPromises()
    await wrapper.get('#product-search').setValue('atiso')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(route.query).toEqual({ search: 'atiso', star: '4' })
    expect(getProducts).toHaveBeenCalledTimes(2)
    expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({
      search: 'atiso', star: 4, page: 1,
    }))
    expect(wrapper.get('.active-filters').text()).toContain('atiso')
  })

  it('applies a star button on top of applied filters without the draft search', async () => {
    route.query = { search: 'coffee', page: '3' }
    const wrapper = mount(ProductsView)
    await flushPromises()
    await wrapper.get('#product-search').setValue('atiso')
    const threeStar = wrapper.findAll('.star-segment button').find((button) => button.text().includes('3 sao'))!
    await threeStar.trigger('click')
    await flushPromises()

    expect(route.query).toEqual({ search: 'coffee', star: '3' })
    expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({ search: 'coffee', star: 3, page: 1 }))
  })

  it('hydrates form, chips and requests on back/forward query changes', async () => {
    route.query = { search: 'coffee', star: '4' }
    const wrapper = mount(ProductsView)
    await flushPromises()
    await wrapper.get('#product-search').setValue('unsubmitted')
    route.query = { search: 'atiso', star: '3', page: '2' }
    await flushPromises()

    expect((wrapper.get('#product-search').element as HTMLInputElement).value).toBe('atiso')
    const pressed = wrapper.findAll('.star-segment button').filter((button) => button.attributes('aria-pressed') === 'true')
    expect(pressed.map((button) => button.text())).toEqual(['3 sao'])
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


  describe('trang thai tai, dong dem va phan trang', () => {
    function deferred<T>() {
      let resolve!: (value: T) => void
      let reject!: (reason?: unknown) => void
      const promise = new Promise<T>((res, rej) => { resolve = res; reject = rej })
      return { promise, resolve, reject }
    }
    type ListResponse = Awaited<ReturnType<typeof getProducts>>

    it('khong khoa nut Tim khi dang tai va van gui duoc bang Enter', async () => {
      const pending = deferred<ListResponse>()
      vi.mocked(getProducts).mockReturnValueOnce(pending.promise)
      const wrapper = mount(ProductsView)
      await flushPromises()
      expect(wrapper.get('.banner-search button').attributes('disabled')).toBeUndefined()
      expect(wrapper.get('.filter-submit').attributes('disabled')).toBeUndefined()
      await wrapper.get('#product-search').setValue('atiso')
      await wrapper.get('.banner-search').trigger('submit')
      await flushPromises()
      expect(route.query).toEqual({ search: 'atiso' })
      expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({ search: 'atiso' }))
      // Kết quả cũ trả về muộn không được ghi đè kết quả mới.
      pending.resolve({ items: [], page: 1, page_size: 12, total: 99 })
      await flushPromises()
      expect(wrapper.get('.result-count').text()).toBe('62 sản phẩm phù hợp')
    })

    it('hien "Dang tai" thay vi 0 san pham, va an dong dem khi loi', async () => {
      const pending = deferred<ListResponse>()
      vi.mocked(getProducts).mockReturnValueOnce(pending.promise)
      const wrapper = mount(ProductsView)
      await flushPromises()
      expect(wrapper.get('.result-count').text()).toBe('Đang tải…')
      expect(wrapper.text()).not.toContain('0 sản phẩm')
      pending.reject(new Error('Network error'))
      await flushPromises()
      expect(wrapper.get('.result-count').isVisible()).toBe(false)
      expect(wrapper.find('.state-box.is-error').exists()).toBe(true)
    })

    it('loi 422 hien thong bao dieu kien loc khong hop le va khong co nut Thu lai', async () => {
      vi.mocked(getProducts).mockRejectedValueOnce(new AxiosError('bad', 'ERR_BAD_REQUEST', undefined, undefined, {
        status: 422, statusText: '', headers: {}, config: { headers: new AxiosHeaders() }, data: {},
      }))
      const wrapper = mount(ProductsView)
      await flushPromises()
      const box = wrapper.get('.state-box.is-error')
      expect(box.text()).toContain('Điều kiện lọc không hợp lệ')
      expect(box.text()).not.toContain('Thử lại')
      expect(box.find('button').text()).toBe('Xóa bộ lọc')
    })

    it('giu phan trang trong DOM khi dang tai va dua focus ve dong ket qua sau khi doi trang', async () => {
      const wrapper = mount(ProductsView, { attachTo: document.body, global: { stubs: { ProductCard: true } } })
      await flushPromises()
      const next = deferred<ListResponse>()
      vi.mocked(getProducts).mockReturnValueOnce(next.promise)
      await wrapper.get('.page-number:nth-child(2)').trigger('click')
      await flushPromises()

      const nav = wrapper.get('nav[aria-label="Phân trang"]')
      expect(nav.attributes('aria-busy')).toBe('true')
      expect(nav.classes()).toContain('is-loading')
      expect(wrapper.findAll('.page-number')).toHaveLength(5)

      next.resolve({ items: [], page: 2, page_size: 12, total: 62 })
      await flushPromises()
      expect(wrapper.get('nav[aria-label="Phân trang"]').attributes('aria-busy')).toBe('false')
      expect(document.activeElement).toBe(wrapper.get('.result-count').element)
      expect(wrapper.get('.result-count').attributes('tabindex')).toBe('-1')
    })

    it('sau khi Thu lai focus nam o dong ket qua, loi lai thi o khoi loi', async () => {
      vi.mocked(getProducts).mockRejectedValueOnce(new Error('x')).mockRejectedValueOnce(new Error('y'))
      const wrapper = mount(ProductsView, { attachTo: document.body })
      await flushPromises()
      await wrapper.get('.state-box.is-error button').trigger('click')
      await flushPromises()
      expect(document.activeElement).toBe(wrapper.get('.state-box.is-error').element)

      vi.mocked(getProducts).mockResolvedValueOnce({ items: [], page: 1, page_size: 12, total: 3 })
      await wrapper.get('.state-box.is-error button').trigger('click')
      await flushPromises()
      expect(document.activeElement).toBe(wrapper.get('.result-count').element)
    })
  })

  describe('bo loc nhap va chuan hoa tham so URL', () => {
    it('doi sap xep chi doi sap xep, giu nguyen o nhap va khong them bo loc chua ap dung', async () => {
      route.query = { search: 'coffee' }
      const wrapper = mount(ProductsView)
      await flushPromises()
      await wrapper.get('#product-district').setValue('xã Tánh Linh')
      await wrapper.get('[aria-label="Giá tối thiểu"]').setValue('900000')
      await wrapper.get('[aria-label="Giá tối đa"]').setValue('100000') // nhap sai: min > max
      await wrapper.get('select.sort-select').setValue('price')
      await flushPromises()

      expect(route.query).toEqual({ search: 'coffee', sort: 'price' })
      expect((wrapper.get('select.sort-select').element as HTMLSelectElement).value).toBe('price')
      expect((wrapper.get('#product-district').element as HTMLInputElement).value).toBe('xã Tánh Linh')
      expect((wrapper.get('[aria-label="Giá tối thiểu"]').element as HTMLInputElement).value).toBe('900000')
    })

    it('chon hang sao khong xoa o nhap khac', async () => {
      const wrapper = mount(ProductsView)
      await flushPromises()
      await wrapper.get('#product-search').setValue('atiso')
      const four = wrapper.findAll('.star-segment button').find((button) => button.text().includes('4 sao'))!
      await four.trigger('click')
      await flushPromises()
      expect(route.query).toEqual({ star: '4' })
      expect((wrapper.get('#product-search').element as HTMLInputElement).value).toBe('atiso')
    })

    it('bo tham so sai tu URL: star, gia khong phai so/am, danh muc khong ton tai', async () => {
      vi.mocked(getCategories).mockResolvedValue({
        items: [{ id: 1, name: 'Đồ uống', slug: 'do-uong' }] as never, page: 1, page_size: 100, total: 1,
      })
      route.query = { star: '2', min_price: 'abc', max_price: '-5', category: 'khong-co', sort: 'bogus' }
      const wrapper = mount(ProductsView)
      await flushPromises()

      expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({
        star: undefined, min_price: undefined, max_price: undefined, sort: 'newest',
      }))
      const chips = wrapper.find('.active-filters').text()
      expect(chips).not.toContain('NaN')
      expect(chips).not.toContain('abc sao')
      expect(chips).not.toContain('2 sao')
      expect(chips).not.toContain('khong-co')
      expect(chips).toContain('Danh mục: không hợp lệ')
      expect(wrapper.findAll('.star-segment button').filter((b) => b.attributes('aria-pressed') === 'true').map((b) => b.text()))
        .toEqual(['Tất cả'])
    })

    it('min lon hon max trong URL: bao loi nhu applyFilters va khong gui khoang gia', async () => {
      route.query = { min_price: '500000', max_price: '1000' }
      const wrapper = mount(ProductsView)
      await flushPromises()
      expect(wrapper.text()).toContain('Giá tối thiểu không được lớn hơn giá tối đa.')
      expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({ min_price: undefined, max_price: undefined }))
      expect(wrapper.find('.active-filters').exists()).toBe(false)
    })

    it('loc gia 1500 duoc ap dung thanh chip, o gia khong co step 1000', async () => {
      const wrapper = mount(ProductsView)
      await flushPromises()
      const min = wrapper.get('[aria-label="Giá tối thiểu"]')
      expect(min.attributes('step')).toBeUndefined()
      expect(min.attributes('inputmode')).toBe('numeric')
      await min.setValue('1500')
      await wrapper.get('form.filter-panel').trigger('submit')
      await flushPromises()
      expect(route.query).toEqual({ min_price: '1500' })
      expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({ min_price: 1500 }))
      expect(wrapper.get('.active-filters').text()).toContain('Giá từ 1.500đ')
    })

    it('gioi han do dai o tim va dia ban theo backend, chip dai co title day du', async () => {
      const longKeyword = 'a'.repeat(300)
      route.query = { search: longKeyword }
      const wrapper = mount(ProductsView)
      await flushPromises()
      expect(wrapper.get('#product-search').attributes('maxlength')).toBe('150')
      expect(wrapper.get('#product-district').attributes('maxlength')).toBe('100')
      expect(getProducts).toHaveBeenLastCalledWith(expect.objectContaining({ search: 'a'.repeat(150) }))
      const chip = wrapper.get('.active-filters button')
      expect(chip.attributes('title')).toBe(`Từ khóa: ${'a'.repeat(150)}`)
      expect(chip.find('.filter-chip-label').exists()).toBe(true)
    })
  })

  describe('ngan keo bo loc tren dien thoai', () => {
    beforeEach(() => {
      vi.stubGlobal('matchMedia', (query: string) => ({
        matches: true, media: query, addEventListener: vi.fn(), removeEventListener: vi.fn(),
      }))
    })
    afterEach(() => {
      vi.unstubAllGlobals()
      document.body.classList.remove('has-modal-open')
    })

    it('mo la hop thoai: focus vao trong, xoay vong Tab, khoa cuoc, Esc dong o moi noi va tra focus', async () => {
      const wrapper = mount(ProductsView, { attachTo: document.body })
      await flushPromises()
      const toggle = wrapper.get('.filter-toggle')
      ;(toggle.element as HTMLElement).focus()
      await toggle.trigger('click')
      await flushPromises()

      const dialog = wrapper.get('.filter-dialog')
      expect(dialog.attributes('role')).toBe('dialog')
      expect(dialog.attributes('aria-modal')).toBe('true')
      expect(wrapper.get(`#${dialog.attributes('aria-labelledby')}`).text()).toBe('Bộ lọc')
      expect(document.body.classList.contains('has-modal-open')).toBe(true)
      expect(wrapper.get('#product-filters').element.contains(document.activeElement)).toBe(true)

      // Tab ở phần tử cuối quay về đầu, Shift+Tab ở đầu sang cuối.
      const items = Array.from(
        wrapper.get('#product-filters').element.querySelectorAll<HTMLElement>('button:not([disabled]), input:not([disabled])'),
      )
      items[items.length - 1].focus()
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true }))
      expect(document.activeElement).toBe(items[0])
      items[0].focus()
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true, cancelable: true }))
      expect(document.activeElement).toBe(items[items.length - 1])

      // Esc nghe o cap document, ke ca khi focus dang o ngoai ngan keo.
      ;(document.activeElement as HTMLElement).blur()
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }))
      await flushPromises()
      expect(wrapper.get('#product-filters').classes()).not.toContain('open')
      expect(wrapper.find('.filter-dialog').attributes('role')).toBeUndefined()
      expect(document.body.classList.contains('has-modal-open')).toBe(false)
      expect(document.activeElement).toBe(toggle.element)
    })

    it('go khoa cuon khi component bi huy trong luc ngan keo dang mo', async () => {
      const wrapper = mount(ProductsView, { attachTo: document.body })
      await flushPromises()
      await wrapper.get('.filter-toggle').trigger('click')
      await flushPromises()
      expect(document.body.classList.contains('has-modal-open')).toBe(true)
      wrapper.unmount()
      expect(document.body.classList.contains('has-modal-open')).toBe(false)
    })
  })

})
