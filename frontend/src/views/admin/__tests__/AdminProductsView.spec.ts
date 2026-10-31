// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import {
  getProductEvidence,
  listAdminProducts,
  listProductChangeRequests,
  moderateProduct,
} from '@/services/product-management'
import AdminProductsView from '@/views/admin/AdminProductsView.vue'

vi.mock('@/services/categories', () => ({
  getCategories: vi.fn().mockResolvedValue({
    items: [
      { id: 1, name: 'Đồ uống', slug: 'do-uong', description: null, icon: null },
      { id: 2, name: 'Thực phẩm', slug: 'thuc-pham', description: null, icon: null },
    ],
    page: 1,
    page_size: 100,
    total: 2,
  }),
}))

vi.mock('@/services/product-management', () => ({
  createDataSource: vi.fn(),
  downloadProductCertificate: vi.fn(),
  getProductEvidence: vi.fn(),
  linkProductEvidence: vi.fn(),
  listDataSources: vi.fn(),
  listAdminProducts: vi.fn(),
  listProductChangeRequests: vi.fn(),
  moderateProduct: vi.fn(),
  moderateProductChangeRequest: vi.fn(),
  unlinkProductEvidence: vi.fn(),
  updateDataSource: vi.fn(),
  updateProductEvidenceLink: vi.fn(),
}))

const pendingProduct = {
  id: 10,
  subject_id: 2,
  category_id: 1,
  name: 'Cà phê Arabica',
  slug: 'ca-phe-arabica',
  star: 4,
  price: '180000',
  unit: 'hộp',
  cert_code: 'OCOP-LD-010',
  cert_issued_at: '2026-01-01',
  cert_expires_at: '2029-01-01',
  issuing_authority: 'Cơ quan có thẩm quyền tỉnh Lâm Đồng',
  certificate_url: 'https://example.com/certificate.pdf',
  vietgap_code: null,
  description: 'Sản phẩm cà phê OCOP Lâm Đồng.',
  story: null,
  ingredients: null,
  usage_instructions: null,
  status: 'pending' as const,
  submitted_at: '2026-09-09T00:00:00Z',
  reviewed_at: null,
  moderation_note: null,
  version: 1,
  category: { id: 1, name: 'Đồ uống', slug: 'do-uong' },
  subject: { id: 2, name: 'HTX Đà Lạt', representative: 'Nguyễn Văn A', tax_code: 'HTX-01' },
  images: [{ id: 1, image_url: 'https://example.com/product.webp', is_primary: true, sort_order: 0 }],
  verification_level: 'A' as const,
  verification_status: 'verified_official_decision' as const,
  evidence_count: 1,
  missing_decision: false,
  missing_issued_at: false,
  created_at: '2026-09-09T00:00:00Z',
  updated_at: '2026-09-09T00:00:00Z',
}

async function mountView(path = '/quan-tri/san-pham') {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/quan-tri/san-pham', name: 'admin-products', component: AdminProductsView }],
  })
  await router.push(path)
  await router.isReady()
  const wrapper = mount(AdminProductsView, { global: { plugins: [router] }, attachTo: document.body })
  await flushPromises()
  return { wrapper, router }
}

const emptyList = { items: [], page: 1, page_size: 20, total: 0 }
const emptyRequests = { items: [], page: 1, page_size: 100, total: 0 }

async function confirmDialog(wrapper: ReturnType<typeof mount>) {
  await flushPromises()
  const button = wrapper.get('.cd-btn--confirm')
  await button.trigger('click')
  await flushPromises()
}

describe('AdminProductsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    document.body.innerHTML = ''
  })

  it('admin mo ho so va duyet hien thi san pham', async () => {
    vi.mocked(listAdminProducts).mockResolvedValue({
      items: [pendingProduct],
      page: 1,
      page_size: 100,
      total: 1,
    })
    vi.mocked(listProductChangeRequests).mockResolvedValue({
      items: [],
      page: 1,
      page_size: 100,
      total: 0,
    })
    vi.mocked(getProductEvidence).mockResolvedValue({
      product_id: 10,
      product_name: 'Cà phê Arabica',
      verification_level: 'A',
      verification_status: 'verified_official_decision',
      evidence_count: 1,
      issues: [],
      sources: [
        {
          evidence_role: 'recognition',
          verification_level: 'A',
          original_address: 'Đà Lạt, Lâm Đồng',
          verified_at: '2026-09-09',
          notes: null,
          source: {
            id: 1,
            title: 'Quyết định công nhận sản phẩm OCOP',
            document_number: '3981/QĐ-UBND',
            issuing_body: 'UBND tỉnh Lâm Đồng',
            source_type: 'official_decision',
            published_at: '2026-08-05',
            source_url: 'https://example.com/decision.pdf',
            local_path: null,
            sha256: null,
            retrieved_at: '2026-09-09',
          },
        },
      ],
    })
    vi.mocked(moderateProduct).mockResolvedValue({
      ...pendingProduct,
      status: 'approved',
      reviewed_at: '2026-09-09T01:00:00Z',
      version: 2,
    })

    const { wrapper } = await mountView()
    expect(wrapper.text()).toContain('Cà phê Arabica')

    const inspectButton = wrapper.findAll('button').find((button) => button.text() === 'Kiểm tra hồ sơ')
    await inspectButton!.trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Cơ quan có thẩm quyền tỉnh Lâm Đồng')
    expect(wrapper.text()).toContain('3981/QĐ-UBND')
    expect(wrapper.text()).toContain('Duyệt hiển thị')
    expect(wrapper.text()).toContain('Yêu cầu bổ sung')
    expect(wrapper.text()).not.toContain('Từ chối hồ sơ')

    const exceptionalButton = wrapper.findAll('button').find((button) => button.text() === 'Hồ sơ không hợp lệ?')
    await exceptionalButton!.trigger('click')
    expect(wrapper.text()).toContain('Từ chối hồ sơ')

    await wrapper.get('.review-modal').trigger('submit')
    await flushPromises()
    expect(moderateProduct).not.toHaveBeenCalled()
    expect(wrapper.get('[role="alertdialog"]').text()).toContain('Xác nhận chấp thuận')
    await confirmDialog(wrapper)
    expect(moderateProduct).toHaveBeenCalledWith(10, {
      status: 'approved',
      note: null,
    })
    wrapper.unmount()
  })

  it('so sanh du lieu dang cong khai voi du lieu chu the de xuat', async () => {
    const currentData = {
      category_id: 1,
      name: 'Cà phê Arabica',
      star: 4,
      price: '180000',
      unit: 'hộp',
      cert_code: 'OCOP-LD-010',
      cert_issued_at: '2026-01-01',
      cert_expires_at: '2029-01-01',
      issuing_authority: 'UBND tỉnh Lâm Đồng',
      certificate_url: 'https://example.com/certificate.pdf',
      vietgap_code: null,
      description: 'Mô tả hiện tại của sản phẩm.',
      story: null,
      ingredients: null,
      usage_instructions: null,
      images: [{ image_url: 'https://example.com/product.webp', is_primary: true, sort_order: 0 }],
    }
    vi.mocked(listAdminProducts).mockResolvedValue({ items: [], page: 1, page_size: 100, total: 0 })
    vi.mocked(listProductChangeRequests).mockResolvedValue({
      items: [
        {
          id: 5,
          product_id: 10,
          subject_id: 2,
          request_type: 'update',
          current_data: currentData,
          proposed_data: { ...currentData, price: '200000', description: 'Mô tả mới.' },
          reason: 'Cập nhật giá bán',
          status: 'pending',
          base_version: 2,
          submitted_at: '2026-09-10T00:00:00Z',
          reviewed_at: null,
          review_note: null,
          product_name: 'Cà phê Arabica',
          subject_name: 'HTX Đà Lạt',
          created_at: '2026-09-10T00:00:00Z',
          updated_at: '2026-09-10T00:00:00Z',
        },
      ],
      page: 1,
      page_size: 100,
      total: 1,
    })

    const { wrapper, router } = await mountView()
    const changesTab = wrapper.findAll('button').find((button) => button.text().includes('Sửa / ngừng'))
    await changesTab!.trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.query.tab).toBe('changes')
    const inspectButton = wrapper.findAll('button').find((button) => button.text() === 'Kiểm tra yêu cầu')
    await inspectButton!.trigger('click')
    await flushPromises()

    const table = wrapper.get('table.comparison-table')
    expect(table.findAll('thead th[scope="col"]')).toHaveLength(3)
    expect(table.findAll('tbody th[scope="row"]')).toHaveLength(11)
    expect(table.find('[role="table"], [role="row"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Đang công khai')
    expect(wrapper.text()).toContain('180.000')
    expect(wrapper.text()).toContain('200.000')
    expect(wrapper.text()).not.toContain('180000')
    // Tên nhóm thay cho mã, ngày theo kiểu Việt Nam, địa chỉ tài liệu rút gọn nhưng vẫn là liên kết.
    expect(table.text()).toContain('Đồ uống')
    expect(table.text()).not.toContain('Mã danh mục')
    expect(table.text()).toContain('1/1/2026')
    const link = table.get('a')
    expect(link.attributes('href')).toBe('https://example.com/certificate.pdf')
    expect(link.text()).toBe('example.com › certificate.pdf')
    const changedRows = table.findAll('tbody tr.changed')
    expect(changedRows).toHaveLength(2)
    expect(changedRows[0].text()).toContain('Đã đổi')
    wrapper.unmount()
  })

  it('phan trang san pham va giu bo loc hien tai', async () => {
    vi.mocked(listAdminProducts).mockResolvedValue({
      items: [pendingProduct],
      page: 1,
      page_size: 20,
      total: 45,
    })
    vi.mocked(listProductChangeRequests).mockResolvedValue({
      items: [],
      page: 1,
      page_size: 100,
      total: 0,
    })

    const { wrapper } = await mountView()
    expect(listAdminProducts).toHaveBeenLastCalledWith(expect.objectContaining({
      page: 1,
      page_size: 20,
      status: 'pending',
    }))
    expect(wrapper.findAll('.filter-panel select')).toHaveLength(1)

    const advancedFilterButton = wrapper.findAll('button').find((button) => button.text() === 'Bộ lọc nâng cao')
    await advancedFilterButton!.trigger('click')
    expect(wrapper.findAll('.filter-panel select')).toHaveLength(4)

    await wrapper.get('.filter-panel').trigger('submit')
    await flushPromises()
    expect(listAdminProducts).toHaveBeenLastCalledWith(expect.objectContaining({
      page: 1,
      page_size: 20,
      status: 'pending',
    }))

    const nextButton = wrapper.findAll('button').find((button) => button.text() === 'Sau')
    await nextButton!.trigger('click')
    await flushPromises()
    expect(listAdminProducts).toHaveBeenLastCalledWith(expect.objectContaining({
      page: 2,
      page_size: 20,
      status: 'pending',
    }))
  })

  it('tải danh sách lỗi thì hiện trạng thái lỗi riêng và nút Thử lại tải lại', async () => {
    vi.mocked(listAdminProducts)
      .mockRejectedValueOnce(new Error('mất mạng'))
      .mockResolvedValueOnce({ items: [pendingProduct], page: 1, page_size: 20, total: 1 })
    vi.mocked(listProductChangeRequests).mockResolvedValue({ items: [], page: 1, page_size: 100, total: 0 })

    const { wrapper } = await mountView()

    const alert = wrapper.get('.status-panel[role="alert"]')
    expect(alert.text()).toContain('Chưa tải được dữ liệu')
    expect(wrapper.text()).not.toContain('Không tìm thấy sản phẩm phù hợp')

    await alert.get('button').trigger('click')
    await flushPromises()
    expect(listAdminProducts).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain(pendingProduct.name)
  })

  it('loc nhanh lien tiep chi hien ket qua cua lan tai moi nhat', async () => {
    const productPage = (name: string) => ({
      items: [{ ...pendingProduct, id: name.length, name }],
      page: 1,
      page_size: 20,
      total: 1,
    })
    let resolveSlow!: (value: ReturnType<typeof productPage>) => void
    vi.mocked(listProductChangeRequests).mockResolvedValue({ items: [], page: 1, page_size: 100, total: 0 })
    vi.mocked(listAdminProducts)
      .mockResolvedValueOnce(productPage('Sản phẩm ban đầu'))
      .mockImplementationOnce(() => new Promise((resolve) => { resolveSlow = resolve }))
      .mockResolvedValueOnce(productPage('Sản phẩm mới nhất'))

    const { wrapper } = await mountView()
    await wrapper.get('form.filter-panel').trigger('submit')
    await wrapper.get('form.filter-panel').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('Sản phẩm mới nhất')

    resolveSlow(productPage('Sản phẩm cũ trả về muộn'))
    await flushPromises()

    expect(wrapper.text()).toContain('Sản phẩm mới nhất')
    expect(wrapper.text()).not.toContain('Sản phẩm cũ trả về muộn')
  })
  it('loi khi duyet hien ngay trong hop thoai, nut bat lai, va bi xoa khi mo lai', async () => {
    vi.mocked(listAdminProducts).mockResolvedValue({ items: [pendingProduct], page: 1, page_size: 20, total: 1 })
    vi.mocked(listProductChangeRequests).mockResolvedValue(emptyRequests)
    vi.mocked(getProductEvidence).mockRejectedValue(new Error('không cần'))
    vi.mocked(moderateProduct).mockRejectedValue(new Error('500'))

    const { wrapper } = await mountView()
    await wrapper.findAll('button').find((button) => button.text() === 'Kiểm tra hồ sơ')!.trigger('click')
    await flushPromises()
    await wrapper.get('.review-modal').trigger('submit')
    await confirmDialog(wrapper)

    expect(moderateProduct).toHaveBeenCalledTimes(1)
    const modalAlert = wrapper.get('.review-modal [role="alert"].modal-error')
    expect(modalAlert.text()).toContain('Không thể xử lý yêu cầu kiểm duyệt.')
    expect(wrapper.find('.alert-danger').exists()).toBe(false)
    expect(wrapper.get('.review-modal .submit-button').attributes('disabled')).toBeUndefined()
    expect(document.activeElement).toBe(modalAlert.element)

    // Đóng rồi mở lại: lỗi cũ không còn.
    await wrapper.findAll('.review-modal footer button')[0].trigger('click')
    await flushPromises()
    expect(wrapper.find('.review-modal').exists()).toBe(false)
    await wrapper.findAll('button').find((button) => button.text() === 'Kiểm tra hồ sơ')!.trigger('click')
    await flushPromises()
    expect(wrapper.find('.modal-error').exists()).toBe(false)
    wrapper.unmount()
  })

  it('thieu phan hoi khi yeu cau bo sung: bao loi trong hop thoai, khong goi API', async () => {
    vi.mocked(listAdminProducts).mockResolvedValue({ items: [pendingProduct], page: 1, page_size: 20, total: 1 })
    vi.mocked(listProductChangeRequests).mockResolvedValue(emptyRequests)
    vi.mocked(getProductEvidence).mockRejectedValue(new Error('x'))

    const { wrapper } = await mountView()
    await wrapper.findAll('button').find((button) => button.text() === 'Kiểm tra hồ sơ')!.trigger('click')
    await flushPromises()
    await wrapper.findAll('.decision-options button')[1].trigger('click')
    await wrapper.get('.review-modal').trigger('submit')
    await flushPromises()
    expect(wrapper.get('.review-modal .modal-error').text()).toContain('Cần nhập nội dung phản hồi')
    expect(moderateProduct).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('Esc khi da go phan hoi thi hoi xac nhan, giu ghi chu neu chon tiep tuc', async () => {
    vi.mocked(listAdminProducts).mockResolvedValue({ items: [pendingProduct], page: 1, page_size: 20, total: 1 })
    vi.mocked(listProductChangeRequests).mockResolvedValue(emptyRequests)
    vi.mocked(getProductEvidence).mockRejectedValue(new Error('x'))

    const { wrapper } = await mountView()
    await wrapper.findAll('button').find((button) => button.text() === 'Kiểm tra hồ sơ')!.trigger('click')
    await flushPromises()
    await wrapper.get('.review-modal textarea').setValue('Cần bổ sung giấy chứng nhận')
    await wrapper.get('.review-modal').trigger('keydown', { key: 'Escape' })
    await flushPromises()
    expect(wrapper.get('[role="alertdialog"]').text()).toContain('Đóng và bỏ phản hồi đã nhập?')

    await wrapper.findAll('.cd-btn')[0].trigger('click')
    await flushPromises()
    expect(wrapper.find('.review-modal').exists()).toBe(true)
    expect((wrapper.get('.review-modal textarea').element as HTMLTextAreaElement).value).toBe('Cần bổ sung giấy chứng nhận')

    await wrapper.get('.review-modal').trigger('keydown', { key: 'Escape' })
    await flushPromises()
    await confirmDialog(wrapper)
    expect(wrapper.find('.review-modal').exists()).toBe(false)
    wrapper.unmount()
  })

  it('doc bo loc tu URL: issue=missing_decision & status=all mo dung danh sach thieu quyet dinh', async () => {
    vi.mocked(listAdminProducts).mockResolvedValue({ items: [pendingProduct], page: 1, page_size: 20, total: 55 })
    vi.mocked(listProductChangeRequests).mockResolvedValue(emptyRequests)

    const { wrapper } = await mountView('/quan-tri/san-pham?status=all&issue=missing_decision')
    expect(listAdminProducts).toHaveBeenCalledWith(expect.objectContaining({ missing_decision: true }))
    const firstCall = vi.mocked(listAdminProducts).mock.calls[0][0]
    expect(firstCall).not.toHaveProperty('status')
    expect((wrapper.get('.basic-filters select').element as HTMLSelectElement).value).toBe('')
    expect(wrapper.text()).toContain('Vấn đề hồ sơ')
    expect((wrapper.findAll('.advanced-filters select')[2].element as HTMLSelectElement).value).toBe('missing_decision')
    wrapper.unmount()
  })

  it('ap dung bo loc ghi vao URL va nut Back khoi phuc', async () => {
    vi.mocked(listAdminProducts).mockResolvedValue({ items: [pendingProduct], page: 1, page_size: 20, total: 1 })
    vi.mocked(listProductChangeRequests).mockResolvedValue(emptyRequests)

    const { wrapper, router } = await mountView()
    await wrapper.get('.basic-filters select').setValue('approved')
    await wrapper.get('input[type="search"]').setValue('arabica')
    await wrapper.get('form.filter-panel').trigger('submit')
    await flushPromises()
    expect(router.currentRoute.value.query).toEqual({ status: 'approved', q: 'arabica' })
    expect(listAdminProducts).toHaveBeenCalledWith(expect.objectContaining({ status: 'approved', search: 'arabica' }))

    vi.mocked(listAdminProducts).mockClear()
    router.back()
    await flushPromises()
    expect(router.currentRoute.value.query).toEqual({})
    expect(listAdminProducts).toHaveBeenCalledWith(expect.objectContaining({ status: 'pending', page_size: 20 }))
    expect((wrapper.get('.basic-filters select').element as HTMLSelectElement).value).toBe('pending')
    wrapper.unmount()
  })

  it('tab=changes tren URL mo thang tab yeu cau', async () => {
    vi.mocked(listAdminProducts).mockResolvedValue(emptyList)
    vi.mocked(listProductChangeRequests).mockResolvedValue({
      items: [
        {
          id: 7,
          product_id: 10,
          subject_id: 2,
          request_type: 'delete',
          current_data: {} as never,
          proposed_data: null,
          reason: 'Ngừng bán',
          status: 'pending',
          base_version: 1,
          submitted_at: '2026-09-10T00:00:00Z',
          reviewed_at: null,
          review_note: null,
          product_name: 'Mật ong',
          subject_name: 'HTX Đà Lạt',
          created_at: '2026-09-10T00:00:00Z',
          updated_at: '2026-09-10T00:00:00Z',
        },
      ],
      page: 1,
      page_size: 100,
      total: 1,
    })
    const { wrapper } = await mountView('/quan-tri/san-pham?tab=changes')
    expect(wrapper.find('form.filter-panel').exists()).toBe(false)
    expect(wrapper.text()).toContain('Mật ong')
    expect(wrapper.text()).toContain('Đề nghị ngừng hiển thị')
    wrapper.unmount()
  })

  it('huy hieu cho xu ly dem rieng theo trang thai cho duyet, khong doi theo bo loc', async () => {
    vi.mocked(listProductChangeRequests).mockResolvedValue(emptyRequests)
    vi.mocked(listAdminProducts).mockImplementation(async (filters) => {
      if (filters?.page_size === 1 && filters.status === 'pending') return { items: [], page: 1, page_size: 1, total: 3 }
      return { items: [pendingProduct], page: 1, page_size: 20, total: 63 }
    })
    const { wrapper } = await mountView('/quan-tri/san-pham?status=approved')
    expect(wrapper.get('.summary-badge').text()).toBe('3 yêu cầu chờ xử lý')
    wrapper.unmount()
  })

  it('expiry=expired chi liet ke san pham da duyet het han (loc phia trinh duyet)', async () => {
    vi.mocked(listProductChangeRequests).mockResolvedValue(emptyRequests)
    const expired = { ...pendingProduct, id: 21, name: 'Trà cũ', status: 'approved' as const, cert_expires_at: '2020-01-01' }
    const valid = { ...pendingProduct, id: 22, name: 'Trà mới', status: 'approved' as const, cert_expires_at: '2099-01-01' }
    vi.mocked(listAdminProducts).mockImplementation(async (filters) => {
      if (filters?.status === 'pending' && filters.page_size === 1) return { items: [], page: 1, page_size: 1, total: 4 }
      return { items: [expired, valid], page: 1, page_size: 100, total: 2 }
    })
    const { wrapper } = await mountView('/quan-tri/san-pham?status=approved&expiry=expired')
    expect(wrapper.text()).toContain('Trà cũ')
    expect(wrapper.text()).not.toContain('Trà mới')
    expect(wrapper.get('.active-filter').text()).toContain('đã hết hạn')
    expect(listAdminProducts).toHaveBeenCalledWith(expect.objectContaining({ status: 'approved', page_size: 100 }))
    wrapper.unmount()
  })

  it('nhan trang thai approved la Da duyet (khong goi la cong khai)', async () => {
    vi.mocked(listAdminProducts).mockResolvedValue({ items: [{ ...pendingProduct, status: 'approved' }], page: 1, page_size: 20, total: 1 })
    vi.mocked(listProductChangeRequests).mockResolvedValue(emptyRequests)
    const { wrapper } = await mountView('/quan-tri/san-pham?status=approved')
    expect(wrapper.get('.status-chip').text()).toBe('Đã duyệt')
    expect(wrapper.get('.filter-hint').text()).toContain('chưa đủ điều kiện hiển thị công khai')
    wrapper.unmount()
  })
})
