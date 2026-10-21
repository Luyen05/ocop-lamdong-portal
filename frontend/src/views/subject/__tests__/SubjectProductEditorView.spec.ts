// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getCategories } from '@/services/categories'
import {
  createProductDraft,
  submitProduct,
  updateProductDraft,
  uploadProductCertificate,
  uploadProductImage,
} from '@/services/product-management'
import type { ManagedProduct } from '@/types/product-management'
import SubjectProductEditorView from '@/views/subject/SubjectProductEditorView.vue'

const router = vi.hoisted(() => ({ push: vi.fn(), replace: vi.fn() }))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: {} }),
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
})
