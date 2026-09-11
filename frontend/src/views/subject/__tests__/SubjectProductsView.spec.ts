// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  cancelProductChangeRequest,
  listMyProducts,
  listProductChangeRequests,
} from '@/services/product-management'
import SubjectProductsView from '@/views/subject/SubjectProductsView.vue'

vi.mock('@/services/product-management', () => ({
  cancelProductChangeRequest: vi.fn(),
  deleteProductDraft: vi.fn(),
  listMyProducts: vi.fn(),
  listProductChangeRequests: vi.fn(),
  requestProductDeletion: vi.fn(),
  resubmitProductChangeRequest: vi.fn(),
  submitProduct: vi.fn(),
}))

const product = {
  id: 20,
  subject_id: 1,
  category_id: 1,
  name: 'Trà atiso',
  slug: 'tra-atiso',
  star: 3,
  price: '90000',
  unit: 'hộp',
  cert_code: 'OCOP-20',
  cert_issued_at: '2026-01-01',
  cert_expires_at: '2029-01-01',
  issuing_authority: 'UBND tỉnh Lâm Đồng',
  certificate_url: 'https://example.com/cert.pdf',
  vietgap_code: null,
  description: 'Sản phẩm trà atiso Lâm Đồng.',
  story: null,
  ingredients: null,
  usage_instructions: null,
  status: 'approved' as const,
  submitted_at: '2026-01-01T00:00:00Z',
  reviewed_at: '2026-01-02T00:00:00Z',
  moderation_note: null,
  version: 2,
  category: { id: 1, name: 'Đồ uống', slug: 'do-uong' },
  subject: { id: 1, name: 'HTX Đà Lạt', representative: 'Nguyễn Văn A', tax_code: null },
  images: [{ id: 1, image_url: 'https://example.com/tea.webp', is_primary: true, sort_order: 0 }],
  verification_level: null,
  verification_status: 'pending_verification' as const,
  evidence_count: 0,
  missing_decision: true,
  missing_issued_at: false,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-02T00:00:00Z',
}

const revisionRequest = {
  id: 8,
  product_id: 20,
  subject_id: 1,
  request_type: 'update' as const,
  proposed_data: null,
  reason: 'Cập nhật bao bì',
  status: 'needs_revision' as const,
  base_version: 2,
  submitted_at: '2026-01-03T00:00:00Z',
  reviewed_at: '2026-01-04T00:00:00Z',
  review_note: 'Bổ sung ảnh chứng nhận.',
  product_name: 'Trà atiso',
  subject_name: 'HTX Đà Lạt',
  created_at: '2026-01-03T00:00:00Z',
  updated_at: '2026-01-04T00:00:00Z',
}

afterEach(() => vi.restoreAllMocks())

describe('SubjectProductsView', () => {
  it('hien thi thao tac bo sung va huy yeu cau can chinh sua', async () => {
    vi.mocked(listMyProducts).mockResolvedValue({ items: [product], page: 1, page_size: 100, total: 1 })
    vi.mocked(listProductChangeRequests).mockResolvedValue({
      items: [revisionRequest],
      page: 1,
      page_size: 100,
      total: 1,
    })
    vi.mocked(cancelProductChangeRequest).mockResolvedValue({
      ...revisionRequest,
      status: 'cancelled',
    })
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    const wrapper = mount(SubjectProductsView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Bổ sung yêu cầu')
    const cancelButton = wrapper.findAll('button').find((button) => button.text() === 'Hủy yêu cầu')
    await cancelButton!.trigger('click')
    await flushPromises()
    expect(cancelProductChangeRequest).toHaveBeenCalledWith(8)
  })
})
