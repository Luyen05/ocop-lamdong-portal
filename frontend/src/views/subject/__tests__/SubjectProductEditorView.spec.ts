// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getCategories } from '@/services/categories'
import {
  createProductDraft,
  getMyProduct,
  submitProduct,
  updateProductDraft,
  uploadProductCertificate,
  uploadProductImage,
} from '@/services/product-management'
import type { ManagedProduct } from '@/types/product-management'
import SubjectProductEditorView from '@/views/subject/SubjectProductEditorView.vue'

const router = vi.hoisted(() => ({ push: vi.fn(), replace: vi.fn() }))
const routeState = vi.hoisted(() => ({ params: {} as Record<string, string> }))

vi.mock('vue-router', () => ({
  useRoute: () => routeState,
  useRouter: () => router,
}))

vi.mock('@/services/categories', () => ({
  getCategories: vi.fn(),
}))

vi.mock('@/services/product-management', () => ({
  createProductDraft: vi.fn(),
  deleteTemporaryProductCertificate: vi.fn(),
  deleteTemporaryProductImage: vi.fn(),
  getProductChangeRequest: vi.fn(),
  getMyProduct: vi.fn(),
  requestProductUpdate: vi.fn(),
  resubmitProductChangeRequest: vi.fn(),
  submitProduct: vi.fn(),
  updateProductDraft: vi.fn(),
  uploadProductCertificate: vi.fn(),
  uploadProductImage: vi.fn(),
}))

describe('SubjectProductEditorView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    routeState.params = {}
    vi.mocked(getCategories).mockResolvedValue({
      items: [{ id: 1, name: 'Đồ uống', slug: 'do-uong', description: null, icon: null }],
      page: 1,
      page_size: 20,
      total: 1,
    })
  })

  it('tai anh hop le va hien thi xem truoc', async () => {
    vi.mocked(uploadProductImage).mockResolvedValue({
      image_url: 'http://localhost:8000/uploads/products/1/abc.png',
      storage_path: 'products/1/0123456789abcdef0123456789abcdef.png',
      content_type: 'image/png',
      size_bytes: 8,
    })
    const wrapper = mount(SubjectProductEditorView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    await flushPromises()

    const file = new File([new Uint8Array([137, 80, 78, 71])], 'san-pham.png', {
      type: 'image/png',
    })
    const input = wrapper.get('.upload-field input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [file] })
    await input.trigger('change')
    await flushPromises()

    expect(uploadProductImage).toHaveBeenCalledWith(file)
    expect(wrapper.get('.image-preview').attributes('src')).toContain('/uploads/products/1/abc.png')
    expect(wrapper.text()).toContain('Ảnh tải lên hệ thống')
  })

  it('chan file qua 5 MB truoc khi gui len may chu', async () => {
    const wrapper = mount(SubjectProductEditorView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    await flushPromises()

    const file = new File([new Uint8Array(5 * 1024 * 1024 + 1)], 'qua-lon.webp', {
      type: 'image/webp',
    })
    const input = wrapper.get('.upload-field input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [file] })
    await input.trigger('change')

    expect(uploadProductImage).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Ảnh không được vượt quá 5 MB')
  })

  it('tai giay chung nhan va cap nhat checklist ho so', async () => {
    vi.mocked(uploadProductCertificate).mockResolvedValue({
      storage_path: 'certificates/1/0123456789abcdef0123456789abcdef.pdf',
      content_type: 'application/pdf',
      size_bytes: 12,
      original_filename: 'chung-nhan-ocop.pdf',
    })
    const wrapper = mount(SubjectProductEditorView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Tiến độ hồ sơ')
    expect(wrapper.text()).toContain('0/3 mục')
    expect(wrapper.find('.primary-button').attributes('disabled')).toBeDefined()

    const file = new File([new Uint8Array([37, 80, 68, 70])], 'chung-nhan-ocop.pdf', {
      type: 'application/pdf',
    })
    const input = wrapper.get('.certificate-upload input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [file] })
    await input.trigger('change')
    await flushPromises()

    expect(uploadProductCertificate).toHaveBeenCalledWith(file)
    expect(wrapper.text()).toContain('chung-nhan-ocop.pdf')
    expect(wrapper.text()).toContain('File riêng tư trên hệ thống')
  })

  it('tao nhap xong ma gui duyet loi thi lan sau sua ban nhap do, khong tao ban trung', async () => {
    vi.mocked(uploadProductImage).mockResolvedValue({
      image_url: 'http://localhost:8000/uploads/products/1/abc.png',
      storage_path: 'products/1/0123456789abcdef0123456789abcdef.png',
      content_type: 'image/png',
      size_bytes: 8,
    })
    vi.mocked(uploadProductCertificate).mockResolvedValue({
      storage_path: 'certificates/1/0123456789abcdef0123456789abcdef.pdf',
      content_type: 'application/pdf',
      size_bytes: 12,
      original_filename: 'chung-nhan.pdf',
    })
    const draft = { id: 42, status: 'draft', category_id: 1, name: 'Trà atiso Đà Lạt' } as ManagedProduct
    vi.mocked(createProductDraft).mockResolvedValue(draft)
    vi.mocked(updateProductDraft).mockResolvedValue(draft)
    vi.mocked(submitProduct)
      .mockRejectedValueOnce(new Error('mất mạng'))
      .mockResolvedValueOnce({ ...draft, status: 'pending' } as ManagedProduct)
    router.replace.mockResolvedValue(undefined)
    const wrapper = mount(SubjectProductEditorView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    await flushPromises()

    await wrapper.get('input[minlength="2"]').setValue('Trà atiso Đà Lạt')
    await wrapper.get('textarea[minlength="10"]').setValue('Trà atiso sấy khô từ vùng trồng Đà Lạt.')
    const selects = wrapper.findAll('select')
    await selects[selects.length - 1]!.setValue('4')
    const certificateInputs = wrapper.findAll('.form-grid input:not([type="file"])')
    const byType = (type: string) => certificateInputs.filter((input) => input.attributes('type') === type)
    await byType('date')[0]!.setValue('2026-01-10')
    await byType('date')[1]!.setValue('2029-01-10')
    const requiredText = wrapper.findAll('input[required]:not([type]):not([minlength])')
    await requiredText[0]!.setValue('QĐ-123/UBND')
    await requiredText[1]!.setValue('UBND tỉnh Lâm Đồng')
    for (const [selector, file] of [
      ['.upload-field input[type="file"]', new File([new Uint8Array([137, 80])], 'a.png', { type: 'image/png' })],
      ['.certificate-upload input[type="file"]', new File([new Uint8Array([37, 80])], 'c.pdf', { type: 'application/pdf' })],
    ] as const) {
      const input = wrapper.get(selector)
      Object.defineProperty(input.element, 'files', { value: [file] })
      await input.trigger('change')
      await flushPromises()
    }
    expect(wrapper.get('.primary-button').attributes('disabled')).toBeUndefined()

    await wrapper.get('form.product-form').trigger('submit')
    await flushPromises()

    expect(createProductDraft).toHaveBeenCalledTimes(1)
    expect(router.replace).toHaveBeenCalledWith({
      name: 'subject-product-edit',
      params: { id: '42' },
      state: { productEditorError: expect.stringContaining('Đã lưu bản nháp nhưng chưa gửi duyệt được') },
    })
    expect(wrapper.get('[role="alert"]').text()).toBe('Không thể lưu thông tin sản phẩm.')

    await wrapper.get('form.product-form').trigger('submit')
    await flushPromises()

    expect(createProductDraft).toHaveBeenCalledTimes(1)
    expect(updateProductDraft).toHaveBeenCalledWith(42, expect.objectContaining({ name: 'Trà atiso Đà Lạt' }))
    expect(submitProduct).toHaveBeenLastCalledWith(42)
    expect(router.push).toHaveBeenCalledWith({ name: 'subject-products', query: { saved: 'submitted' } })
  })

  it('tao moi chi chon duoc danh muc dang hien', async () => {
    const wrapper = mount(SubjectProductEditorView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    await flushPromises()

    const options = wrapper.get('select').findAll('option').map((option) => option.text())
    expect(options).toEqual(['Đồ uống'])
  })

  it('sua san pham thuoc danh muc dang an van giu nguyen danh muc', async () => {
    routeState.params = { id: '7' }
    vi.mocked(getMyProduct).mockResolvedValue({
      id: 7,
      category_id: 9,
      category: { id: 9, name: 'Sinh vật cảnh', slug: 'sinh-vat-canh' },
      name: 'Lan hồ điệp',
      star: null,
      price: null,
      unit: null,
      cert_code: null,
      cert_issued_at: null,
      cert_expires_at: null,
      issuing_authority: null,
      certificate_url: null,
      certificate_storage_path: null,
      vietgap_code: null,
      description: null,
      story: null,
      ingredients: null,
      usage_instructions: null,
      images: [],
      status: 'draft',
    } as unknown as ManagedProduct)
    const wrapper = mount(SubjectProductEditorView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    await flushPromises()

    const select = wrapper.get('select').element as HTMLSelectElement
    expect(Array.from(select.options).map((option) => option.text)).toEqual([
      'Đồ uống',
      'Sinh vật cảnh (đang tạm ẩn)',
    ])
    expect(select.value).toBe('9')
  })

  it('maxlength theo schema backend, o gia khong con step=1000 (B15)', async () => {
    const wrapper = mount(SubjectProductEditorView, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
    await flushPromises()
    const limits: Array<[string, string]> = [
      ['Tên sản phẩm', '255'],
      ['Đơn vị tính', '50'],
      ['Mô tả sản phẩm', '5000'],
      ['Câu chuyện sản phẩm', '10000'],
      ['Thành phần', '5000'],
      ['Hướng dẫn sử dụng', '5000'],
      ['Mã chứng nhận', '100'],
      ['Cơ quan công nhận', '255'],
      ['Mã VietGAP', '100'],
    ]
    for (const [label, max] of limits) {
      const field = wrapper.findAll('label').find((item) => item.text().startsWith(label))!.find('input, textarea')
      expect(field.attributes('maxlength'), label).toBe(max)
    }
    const price = wrapper.get('input[type="number"]')
    expect(price.attributes('step')).toBeUndefined()
    expect(price.attributes('inputmode')).toBe('numeric')
    expect(price.attributes('min')).toBe('0')
  })

  it('khi chua du dieu kien: liet ke truong con thieu va gan aria-describedby vao nut gui duyet (B15)', async () => {
    const wrapper = mount(SubjectProductEditorView, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
    await flushPromises()

    const hint = wrapper.get('#submit-missing')
    expect(hint.text()).toContain('Còn thiếu:')
    for (const field of ['tên sản phẩm', 'mô tả sản phẩm', 'hạng sao', 'mã chứng nhận', 'ngày cấp', 'ngày hết hạn', 'cơ quan công nhận', 'giấy chứng nhận', 'ảnh đại diện']) {
      expect(hint.text()).toContain(field)
    }
    const submit = wrapper.get('button.primary-button')
    expect(submit.attributes('disabled')).toBeDefined()
    expect(submit.attributes('aria-describedby')).toBe('submit-missing')

    await wrapper.findAll('label').find((item) => item.text().startsWith('Tên sản phẩm'))!.get('input').setValue('Cà phê Arabica')
    expect(wrapper.get('#submit-missing').text()).not.toContain('tên sản phẩm')
  })

  it('luu nhap khi ten trong: bao loi, danh dau o ten, cuon vao khung nhin (A9, C14)', async () => {
    const scroll = vi.fn()
    ;(Element.prototype as unknown as { scrollIntoView: unknown }).scrollIntoView = scroll
    const wrapper = mount(SubjectProductEditorView, {
      attachTo: document.body,
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    await flushPromises()
    await wrapper.get('.secondary-button').trigger('click')
    await flushPromises()

    const alert = wrapper.get('[role="alert"][data-flash="error"]')
    expect(alert.text()).toContain('Cần nhập tên')
    expect(scroll).toHaveBeenCalledWith({ block: 'center', behavior: expect.any(String) })
    expect(document.activeElement).toBe(alert.element)
    const name = wrapper.findAll('label').find((item) => item.text().startsWith('Tên sản phẩm'))!.get('input')
    expect(name.attributes('aria-invalid')).toBe('true')
    expect(createProductDraft).not.toHaveBeenCalled()
    wrapper.unmount()
  })
})
