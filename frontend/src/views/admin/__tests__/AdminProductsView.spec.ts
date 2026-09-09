// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import {
  listAdminProducts,
  listProductChangeRequests,
  moderateProduct,
} from '@/services/product-management'
import AdminProductsView from '@/views/admin/AdminProductsView.vue'

vi.mock('@/services/product-management', () => ({
  listAdminProducts: vi.fn(),
  listProductChangeRequests: vi.fn(),
  moderateProduct: vi.fn(),
  moderateProductChangeRequest: vi.fn(),
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
  created_at: '2026-09-09T00:00:00Z',
  updated_at: '2026-09-09T00:00:00Z',
}

describe('AdminProductsView', () => {
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
    vi.mocked(moderateProduct).mockResolvedValue({
      ...pendingProduct,
      status: 'approved',
      reviewed_at: '2026-09-09T01:00:00Z',
      version: 2,
    })

    const wrapper = mount(AdminProductsView)
    await flushPromises()
    expect(wrapper.text()).toContain('Cà phê Arabica')

    const inspectButton = wrapper.findAll('button').find((button) => button.text() === 'Kiểm tra hồ sơ')
    await inspectButton!.trigger('click')
    expect(wrapper.text()).toContain('Cơ quan có thẩm quyền tỉnh Lâm Đồng')

    await wrapper.get('.review-modal').trigger('submit')
    await flushPromises()
    expect(moderateProduct).toHaveBeenCalledWith(10, {
      status: 'approved',
      note: null,
    })
  })
})
