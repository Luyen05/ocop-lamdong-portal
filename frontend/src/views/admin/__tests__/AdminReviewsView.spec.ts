// @vitest-environment jsdom
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { listAdminReviews, moderateReview } from '@/services/reviews'
import type { AdminReview, AdminReviewListResponse } from '@/types/review'
import AdminReviewsView from '@/views/admin/AdminReviewsView.vue'

enableAutoUnmount(afterEach)

vi.mock('@/services/reviews', () => ({
  listAdminReviews: vi.fn(),
  moderateReview: vi.fn(),
}))

const RouterLinkStub = defineComponent({
  name: 'RouterLink',
  props: ['to'],
  template: '<a :href="to"><slot /></a>',
})

const pendingReview: AdminReview = {
  id: 5,
  rating: 4,
  comment: 'Trà thơm, đóng gói cẩn thận.',
  status: 'pending',
  rejection_reason: null,
  reviewed_at: null,
  created_at: '2026-10-15T00:00:00Z',
  updated_at: '2026-10-15T00:00:00Z',
  target: { type: 'product', id: 1, name: 'Trà xanh Cầu Đất', slug: 'tra-xanh-cau-dat' },
  author: { id: 3, full_name: 'Trần Thị Khách', email: 'khach@example.com' },
  reviewed_by_name: null,
}

function listResponse(items: AdminReview[] = [pendingReview]): AdminReviewListResponse {
  return { items, page: 1, page_size: 10, total: items.length }
}

function mountView() {
  return mount(AdminReviewsView, { attachTo: document.body, global: { stubs: { RouterLink: RouterLinkStub } } })
}

describe('AdminReviewsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(listAdminReviews).mockResolvedValue(listResponse())
  })

  it('mac dinh loc danh gia cho duyet va hien thong tin nguoi viet, doi tuong', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(listAdminReviews).toHaveBeenCalledWith({ page: 1, page_size: 10, status: 'pending', target: undefined, q: undefined })
    const row = wrapper.get('[data-test="row-5"]')
    expect(row.text()).toContain('Trà thơm, đóng gói cẩn thận.')
    expect(row.text()).toContain('khach@example.com')
    expect(row.text()).toContain('Sản phẩm OCOP')
    expect(row.get('a').attributes('href')).toBe('/san-pham/tra-xanh-cau-dat')
    expect(row.text()).toContain('Chờ duyệt')
  })

  it('loc theo loai, trang thai va tu khoa', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.get('[data-test="target-filter"]').setValue('location')
    await flushPromises()
    expect(listAdminReviews).toHaveBeenLastCalledWith(expect.objectContaining({ target: 'location', status: 'pending' }))

    await wrapper.get('[data-test="status-filter"]').setValue('')
    await wrapper.get('input[type="search"]').setValue('  Cầu Đất ')
    await wrapper.get('form.filter-bar').trigger('submit')
    await flushPromises()
    expect(listAdminReviews).toHaveBeenLastCalledWith({ page: 1, page_size: 10, status: undefined, target: 'location', q: 'Cầu Đất' })
  })

  it('bo ket qua cu khi loc nhanh', async () => {
    let resolveSlow: (value: AdminReviewListResponse) => void = () => {}
    vi.mocked(listAdminReviews)
      .mockResolvedValueOnce(listResponse())
      .mockReturnValueOnce(new Promise((resolve) => { resolveSlow = resolve }))
      .mockResolvedValueOnce(listResponse([]))
    const wrapper = mountView()
    await flushPromises()

    await wrapper.get('[data-test="status-filter"]').setValue('approved')
    await wrapper.get('[data-test="status-filter"]').setValue('rejected')
    await flushPromises()
    resolveSlow(listResponse([{ ...pendingReview, id: 99, status: 'approved' }]))
    await flushPromises()

    expect(wrapper.find('[data-test="row-99"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Không có đánh giá phù hợp với bộ lọc')
  })

  it('duyet danh gia roi tai lai danh sach', async () => {
    vi.mocked(moderateReview).mockResolvedValue({ ...pendingReview, status: 'approved' })
    const wrapper = mountView()
    await flushPromises()
    vi.mocked(listAdminReviews).mockResolvedValue(listResponse([]))

    await wrapper.get('[data-test="approve"]').trigger('click')
    await flushPromises()

    expect(moderateReview).toHaveBeenCalledWith(5, { action: 'approve' })
    expect(wrapper.get('.alert-success').text()).toContain('Đã duyệt đánh giá của Trần Thị Khách.')
    expect(wrapper.text()).toContain('Không còn đánh giá chờ duyệt')
  })

  it('tu choi phai nhap ly do trong hop thoai', async () => {
    vi.mocked(moderateReview).mockResolvedValue({ ...pendingReview, status: 'rejected', rejection_reason: 'Có quảng cáo.' })
    const wrapper = mountView()
    await flushPromises()

    await wrapper.get('[data-test="reject"]').trigger('click')
    await flushPromises()
    const dialog = wrapper.get('[role="dialog"]')
    expect(dialog.attributes('aria-modal')).toBe('true')
    expect(dialog.get('label').attributes('for')).toBe('reject-reason')

    await dialog.get('form').trigger('submit')
    expect(moderateReview).not.toHaveBeenCalled()
    expect(dialog.get('[role="alert"]').text()).toContain('Vui lòng nhập lý do từ chối')

    await dialog.get('textarea').setValue('  Có quảng cáo.  ')
    await dialog.get('form').trigger('submit')
    await flushPromises()
    expect(moderateReview).toHaveBeenCalledWith(5, { action: 'reject', reason: 'Có quảng cáo.' })
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
    expect(wrapper.get('.alert-success').text()).toContain('Đã từ chối đánh giá của Trần Thị Khách.')
  })

  it('bao loi va thu lai', async () => {
    vi.mocked(listAdminReviews).mockRejectedValueOnce(new Error('network'))
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('Không thể tải danh sách đánh giá.')

    await wrapper.get('.status-retry').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-test="row-5"]').exists()).toBe(true)
  })
})
