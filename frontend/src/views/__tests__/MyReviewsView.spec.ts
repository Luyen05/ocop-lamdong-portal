// @vitest-environment jsdom
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { documentTitleFor } from '@/router/titles'
import { deleteReview, listMyReviews, updateReview } from '@/services/reviews'
import type { MyReview } from '@/types/review'
import MyReviewsView from '@/views/MyReviewsView.vue'

enableAutoUnmount(afterEach)

vi.mock('@/services/reviews', () => ({
  listMyReviews: vi.fn(),
  updateReview: vi.fn(),
  deleteReview: vi.fn(),
}))

const RouterLinkStub = defineComponent({
  name: 'RouterLink',
  props: ['to'],
  template: '<a :href="typeof to === \'string\' ? to : \'#\'"><slot /></a>',
})

const productReview: MyReview = {
  id: 1,
  rating: 5,
  comment: 'Trà thơm, vị hậu ngọt, đóng gói đẹp.',
  status: 'approved',
  rejection_reason: null,
  reviewed_at: '2026-10-12T00:00:00Z',
  created_at: '2026-10-10T00:00:00Z',
  updated_at: '2026-10-12T00:00:00Z',
  target: { type: 'product', id: 4, name: 'Trà xanh Cầu Đất', slug: 'tra-xanh-cau-dat' },
}

const locationReview: MyReview = {
  id: 2,
  rating: 2,
  comment: 'Đường vào hơi khó đi.',
  status: 'rejected',
  rejection_reason: 'Vui lòng mô tả trải nghiệm tại điểm.',
  reviewed_at: '2026-10-13T00:00:00Z',
  created_at: '2026-10-11T00:00:00Z',
  updated_at: '2026-10-13T00:00:00Z',
  target: { type: 'location', id: 7, name: 'Cầu Đất Farm', slug: 'cau-dat-farm' },
}

function mountView() {
  return mount(MyReviewsView, { global: { stubs: { RouterLink: RouterLinkStub } } })
}

describe('MyReviewsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(listMyReviews).mockResolvedValue({ items: [productReview, locationReview], page: 1, page_size: 10, total: 2 })
  })

  it('co tieu de trang', () => {
    expect(documentTitleFor('my-reviews')).toContain('Đánh giá của tôi')
  })

  it('liet ke danh gia moi trang thai kem lien ket va ly do tu choi', async () => {
    const wrapper = mountView()
    expect(wrapper.find('[role="status"]').exists()).toBe(true)
    await flushPromises()

    expect(listMyReviews).toHaveBeenCalledWith({ page: 1, page_size: 10 })
    const first = wrapper.get('[data-test="review-1"]')
    expect(first.text()).toContain('Sản phẩm OCOP')
    expect(first.text()).toContain('Đang hiển thị')
    expect(first.get('a.target-link').attributes('href')).toBe('/san-pham/tra-xanh-cau-dat')

    const second = wrapper.get('[data-test="review-2"]')
    expect(second.text()).toContain('Điểm du lịch')
    expect(second.get('a.target-link').attributes('href')).toBe('/diem-du-lich/cau-dat-farm')
    expect(second.get('[data-test="rejection-reason"]').text()).toContain('Bị từ chối: Vui lòng mô tả trải nghiệm tại điểm.')
  })

  it('sua danh gia thi quay ve cho duyet', async () => {
    vi.mocked(updateReview).mockResolvedValue({ ...locationReview, comment: 'Vườn đẹp, nhân viên hướng dẫn kỹ.', status: 'pending', rejection_reason: null })
    const wrapper = mountView()
    await flushPromises()

    const card = wrapper.get('[data-test="review-2"]')
    await card.get('[data-test="edit"]').trigger('click')
    await card.get('textarea').setValue('Vườn đẹp, nhân viên hướng dẫn kỹ.')
    await card.get('form').trigger('submit')
    await flushPromises()

    expect(updateReview).toHaveBeenCalledWith(2, { rating: 2, comment: 'Vườn đẹp, nhân viên hướng dẫn kỹ.' })
    expect(wrapper.get('[data-test="review-2"]').text()).toContain('Đang chờ duyệt')
    expect(wrapper.get('.notice').text()).toContain('sau khi được duyệt')
  })

  it('xoa danh gia sau khi xac nhan', async () => {
    vi.mocked(deleteReview).mockResolvedValue()
    const wrapper = mountView()
    await flushPromises()

    await wrapper.get('[data-test="review-1"] [data-test="delete"]').trigger('click')
    expect(deleteReview).not.toHaveBeenCalled()
    await wrapper.get('[data-test="confirm-delete"]').trigger('click')
    await flushPromises()

    expect(deleteReview).toHaveBeenCalledWith(1)
    expect(wrapper.find('[data-test="review-1"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Đã xóa đánh giá cho "Trà xanh Cầu Đất".')
  })

  it('bao rong co duong dan tim san pham, diem du lich', async () => {
    vi.mocked(listMyReviews).mockResolvedValue({ items: [], page: 1, page_size: 10, total: 0 })
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('Bạn chưa viết đánh giá nào')
    expect(wrapper.findAll('.empty-actions a').map((link) => link.attributes('href'))).toEqual(['/san-pham', '/diem-du-lich'])
  })

  it('bao loi va thu lai', async () => {
    vi.mocked(listMyReviews).mockRejectedValueOnce(new Error('network'))
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('Chưa tải được đánh giá của bạn')

    await wrapper.get('.status-retry').trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.my-review-card')).toHaveLength(2)
  })

  it('xem them tai trang tiep theo', async () => {
    vi.mocked(listMyReviews)
      .mockResolvedValueOnce({ items: [productReview], page: 1, page_size: 10, total: 2 })
      .mockResolvedValueOnce({ items: [locationReview], page: 2, page_size: 10, total: 2 })
    const wrapper = mountView()
    await flushPromises()
    await wrapper.get('[data-test="load-more"]').trigger('click')
    await flushPromises()

    expect(listMyReviews).toHaveBeenLastCalledWith({ page: 2, page_size: 10 })
    expect(wrapper.findAll('.my-review-card')).toHaveLength(2)
    expect(wrapper.find('[data-test="load-more"]').exists()).toBe(false)
  })
})
