// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getCategories } from '@/services/categories'
import { uploadProductCertificate, uploadProductImage } from '@/services/product-management'
import SubjectProductEditorView from '@/views/subject/SubjectProductEditorView.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: {} }),
  useRouter: () => ({ push: vi.fn() }),
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
})
