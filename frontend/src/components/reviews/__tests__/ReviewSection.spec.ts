// @vitest-environment jsdom
import { AxiosError, AxiosHeaders } from 'axios'
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { defineComponent, type Ref } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import ReviewSection from '@/components/reviews/ReviewSection.vue'
import {
  createReview,
  deleteReview,
  getPublicReviews,
  listMyReviews,
  updateReview,
} from '@/services/reviews'
import { getMySubjectApplication } from '@/services/subjects'
import { authStore } from '@/stores/auth'
import type { User } from '@/types/auth'
import type { MyReview, PublicReviewListResponse } from '@/types/review'
import type { SubjectApplication } from '@/types/subject'

enableAutoUnmount(afterEach)

vi.mock('vue-router', () => ({
  useRoute: () => ({ fullPath: '/san-pham/tra-xanh-cau-dat' }),
}))
vi.mock('@/services/reviews', () => ({
  getPublicReviews: vi.fn(),
  listMyReviews: vi.fn(),
  createReview: vi.fn(),
  updateReview: vi.fn(),
  deleteReview: vi.fn(),
}))
vi.mock('@/services/subjects', () => ({ getMySubjectApplication: vi.fn() }))
vi.mock('@/stores/auth', async () => {
  const { computed, ref } = await import('vue')
  const currentUser = ref<User | null>(null)
  return { authStore: { currentUser, isAuthenticated: computed(() => Boolean(currentUser.value)) } }
})

const currentUser = authStore.currentUser as unknown as Ref<User | null>

const RouterLinkStub = defineComponent({
  name: 'RouterLink',
  props: ['to'],
  template: '<a :data-to="JSON.stringify(to)"><slot /></a>',
})

function makeUser(role: User['role'], id = 7): User {
  return {
    id,
    email: `${role}@example.com`,
    full_name: 'Trần Thị Khách',
    phone: null,
    avatar_url: null,
    is_active: true,
    role,
    created_at: '2026-10-01T00:00:00Z',
    updated_at: '2026-10-01T00:00:00Z',
  }
}

function publicPage(overrides: Partial<PublicReviewListResponse> = {}): PublicReviewListResponse {
  return {
    items: [
      { id: 11, rating: 5, comment: 'Trà thơm, vị hậu ngọt.', author_name: 'Lê Văn Hai', created_at: '2026-10-10T08:00:00Z', updated_at: '2026-10-10T08:00:00Z' },
      { id: 12, rating: 4, comment: '<b>Đóng gói</b> cẩn thận.', author_name: 'Phạm Thu', created_at: '2026-10-09T08:00:00Z', updated_at: '2026-10-09T08:00:00Z' },
    ],
    page: 1,
    page_size: 5,
    total: 2,
    summary: { average: 4.5, count: 2, distribution: { 1: 0, 2: 0, 3: 0, 4: 1, 5: 1 } },
    ...overrides,
  }
}

const myPending: MyReview = {
  id: 30,
  rating: 4,
  comment: 'Ngon, sẽ mua lại lần sau.',
  status: 'pending',
  rejection_reason: null,
  reviewed_at: null,
  created_at: '2026-10-11T00:00:00Z',
  updated_at: '2026-10-11T00:00:00Z',
  target: { type: 'product', id: 1, name: 'Trà xanh Cầu Đất', slug: 'tra-xanh-cau-dat' },
}

function mountSection(props: Record<string, unknown> = {}) {
  return mount(ReviewSection, {
    props: { targetType: 'product', targetId: 1, ownerSubjectId: 3, ...props },
    global: { stubs: { RouterLink: RouterLinkStub } },
  })
}

function axiosError(status: number, data: Record<string, unknown>) {
  return new AxiosError('error', 'ERR_BAD_REQUEST', undefined, undefined, {
    status,
    statusText: '',
    headers: {},
    config: { headers: new AxiosHeaders() },
    data,
  })
}

describe('ReviewSection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    currentUser.value = null
    vi.mocked(getPublicReviews).mockResolvedValue(publicPage())
    vi.mocked(listMyReviews).mockResolvedValue({ items: [], page: 1, page_size: 1, total: 0 })
  })

  it('hien tom tat sao, danh sach da duyet va nut dang nhap khi chua dang nhap', async () => {
    const wrapper = mountSection()
    expect(wrapper.find('[role="status"]').text()).toContain('Đang tải đánh giá')
    await flushPromises()

    expect(getPublicReviews).toHaveBeenCalledWith('product', 1, { page: 1, page_size: 5 })
    expect(listMyReviews).not.toHaveBeenCalled()
    expect(wrapper.get('.summary-score').text()).toContain('4,5')
    expect(wrapper.text()).toContain('2 đánh giá đã duyệt')
    expect(wrapper.findAll('.distribution li').map((row) => row.text())).toEqual([
      '5 sao1 đánh giá', '4 sao1 đánh giá', '3 sao0 đánh giá', '2 sao0 đánh giá', '1 sao0 đánh giá',
    ])
    expect(wrapper.findAll('.review-item')).toHaveLength(2)
    // Nội dung hiển thị dạng chữ thuần, không chèn HTML.
    expect(wrapper.find('.review-item b').exists()).toBe(false)
    expect(wrapper.text()).toContain('<b>Đóng gói</b> cẩn thận.')
    const login = wrapper.get('[data-test="login-to-review"]')
    expect(login.text()).toBe('Đăng nhập để đánh giá')
    expect(JSON.parse(login.attributes('data-to') ?? '{}')).toEqual({
      path: '/dang-nhap',
      query: { redirect: '/san-pham/tra-xanh-cau-dat' },
    })
    expect(wrapper.find('form').exists()).toBe(false)
  })

  it('bao rong khi chua co danh gia nao', async () => {
    vi.mocked(getPublicReviews).mockResolvedValue(
      publicPage({ items: [], total: 0, summary: { average: 0, count: 0, distribution: { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 } } }),
    )
    const wrapper = mountSection()
    await flushPromises()
    expect(wrapper.text()).toContain('Chưa có đánh giá nào')
    expect(wrapper.find('.distribution').exists()).toBe(false)
  })

  it('bao loi va cho thu lai', async () => {
    vi.mocked(getPublicReviews).mockRejectedValueOnce(new Error('network'))
    const wrapper = mountSection()
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('Chưa tải được đánh giá')

    await wrapper.get('.status-retry').trigger('click')
    await flushPromises()
    expect(getPublicReviews).toHaveBeenCalledTimes(2)
    expect(wrapper.findAll('.review-item')).toHaveLength(2)
  })

  it('xem them noi tiep trang sau', async () => {
    vi.mocked(getPublicReviews)
      .mockResolvedValueOnce(publicPage({ total: 3 }))
      .mockResolvedValueOnce(publicPage({
        page: 2,
        total: 3,
        items: [{ id: 13, rating: 3, comment: 'Giá hơi cao.', author_name: 'Ngô An', created_at: '2026-10-01T00:00:00Z', updated_at: '2026-10-01T00:00:00Z' }],
      }))
    const wrapper = mountSection()
    await flushPromises()
    expect(wrapper.get('[data-test="load-more"]').text()).toContain('Xem thêm đánh giá (1)')

    await wrapper.get('[data-test="load-more"]').trigger('click')
    await flushPromises()
    expect(getPublicReviews).toHaveBeenLastCalledWith('product', 1, { page: 2, page_size: 5 })
    expect(wrapper.findAll('.review-item')).toHaveLength(3)
    expect(wrapper.find('[data-test="load-more"]').exists()).toBe(false)
  })

  it('kiem tra form roi gui danh gia moi o trang thai cho duyet', async () => {
    currentUser.value = makeUser('user')
    vi.mocked(createReview).mockResolvedValue(myPending)
    const wrapper = mountSection()
    await flushPromises()
    expect(listMyReviews).toHaveBeenCalledWith({ product_id: 1, page_size: 1 })

    await wrapper.get('form').trigger('submit')
    expect(wrapper.text()).toContain('Vui lòng chọn số sao.')
    expect(wrapper.text()).toContain('Nhận xét cần ít nhất 10 ký tự.')
    expect(createReview).not.toHaveBeenCalled()

    const radios = wrapper.findAll('input[type="radio"]')
    expect(radios).toHaveLength(5)
    expect(wrapper.get('legend').text()).toContain('Bạn chấm mấy sao?')
    await radios[3].setValue(true)
    await wrapper.get('textarea').setValue('  Ngon, sẽ mua lại lần sau.  ')
    expect(wrapper.get('.char-count').text()).toBe('25/1000 ký tự')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(createReview).toHaveBeenCalledWith('product', 1, { rating: 4, comment: 'Ngon, sẽ mua lại lần sau.' })
    expect(wrapper.get('[role="status"]').text()).toContain('sau khi được duyệt')
    expect(wrapper.get('[data-test="my-review"]').text()).toContain('Đang chờ duyệt')
  })

  it('hien danh gia bi tu choi kem ly do, cho sua va xoa', async () => {
    currentUser.value = makeUser('user')
    vi.mocked(listMyReviews).mockResolvedValue({
      items: [{ ...myPending, status: 'rejected', rejection_reason: 'Thiếu trải nghiệm thực tế.' }],
      page: 1,
      page_size: 1,
      total: 1,
    })
    vi.mocked(updateReview).mockResolvedValue({ ...myPending, rating: 5 })
    vi.mocked(deleteReview).mockResolvedValue()
    const wrapper = mountSection()
    await flushPromises()

    expect(wrapper.get('[data-test="my-review"]').text()).toContain('Bị từ chối')
    expect(wrapper.get('[data-test="rejection-reason"]').text()).toBe('Bị từ chối: Thiếu trải nghiệm thực tế.')

    await wrapper.get('[data-test="edit-review"]').trigger('click')
    expect((wrapper.get('textarea').element as HTMLTextAreaElement).value).toBe(myPending.comment)
    await wrapper.findAll('input[type="radio"]')[4].setValue(true)
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(updateReview).toHaveBeenCalledWith(30, { rating: 5, comment: myPending.comment })
    expect(wrapper.get('[data-test="my-review"]').text()).toContain('Đang chờ duyệt')

    await wrapper.get('[data-test="delete-review"]').trigger('click')
    await wrapper.get('[data-test="confirm-delete"]').trigger('click')
    await flushPromises()
    expect(deleteReview).toHaveBeenCalledWith(30)
    expect(wrapper.find('[data-test="my-review"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Đã xóa đánh giá của bạn.')
  })

  it('bao trung khi da danh gia o noi khac va hien lai danh gia cu', async () => {
    currentUser.value = makeUser('user')
    vi.mocked(createReview).mockRejectedValue(
      axiosError(409, { code: 'REVIEW_ALREADY_EXISTS', message: 'Bạn đã đánh giá mục này.', details: { review_id: 30 } }),
    )
    const wrapper = mountSection()
    await flushPromises()
    vi.mocked(listMyReviews).mockResolvedValue({ items: [myPending], page: 1, page_size: 1, total: 1 })

    await wrapper.findAll('input[type="radio"]')[2].setValue(true)
    await wrapper.get('textarea').setValue('Một nhận xét đủ dài.')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(listMyReviews).toHaveBeenCalledTimes(2)
    expect(wrapper.get('[data-test="my-review"]').text()).toContain('Bạn đã đánh giá mục này.')
  })

  it('chu the xem san pham cua minh thi hien ghi chu, khong co form', async () => {
    currentUser.value = makeUser('subject')
    vi.mocked(getMySubjectApplication).mockResolvedValue({ id: 3 } as SubjectApplication)
    const wrapper = mountSection({ ownerSubjectId: 3 })
    await flushPromises()

    expect(wrapper.get('[data-test="owner-note"]').text()).toContain('không tự đánh giá')
    expect(wrapper.find('form').exists()).toBe(false)
  })

  it('chu the khac van viet duoc danh gia', async () => {
    currentUser.value = makeUser('subject')
    vi.mocked(getMySubjectApplication).mockResolvedValue({ id: 9 } as SubjectApplication)
    const wrapper = mountSection({ ownerSubjectId: 3 })
    await flushPromises()
    expect(wrapper.find('[data-test="owner-note"]').exists()).toBe(false)
    expect(wrapper.find('form').exists()).toBe(true)
  })

  it('admin chi thay ghi chu, khong goi danh gia cua toi', async () => {
    currentUser.value = makeUser('admin')
    const wrapper = mountSection()
    await flushPromises()
    expect(listMyReviews).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Tài khoản quản trị không viết đánh giá')
    expect(wrapper.find('form').exists()).toBe(false)
  })

  it('bo ket qua cu khi doi sang doi tuong khac', async () => {
    let resolveFirst: (value: PublicReviewListResponse) => void = () => {}
    vi.mocked(getPublicReviews)
      .mockReturnValueOnce(new Promise((resolve) => { resolveFirst = resolve }))
      .mockResolvedValueOnce(publicPage({ items: [], total: 0 }))
    const wrapper = mountSection()
    await wrapper.setProps({ targetType: 'location', targetId: 2 })
    await flushPromises()
    resolveFirst(publicPage())
    await flushPromises()

    expect(getPublicReviews).toHaveBeenLastCalledWith('location', 2, { page: 1, page_size: 5 })
    expect(wrapper.findAll('.review-item')).toHaveLength(0)
    expect(wrapper.text()).toContain('Chưa có đánh giá nào')
  })

  describe('chuyen focus', () => {
    function mountAttached() {
      return mount(ReviewSection, {
        props: { targetType: 'product', targetId: 1, ownerSubjectId: 3 },
        global: { stubs: { RouterLink: RouterLinkStub } },
        attachTo: document.body,
      })
    }

    it('gui thieu thi focus o loi dau tien (sao roi toi nhan xet), loi nhan xet co role=alert', async () => {
      currentUser.value = makeUser('user')
      const wrapper = mountAttached()
      await flushPromises()

      await wrapper.get('form').trigger('submit')
      await flushPromises()
      expect(document.activeElement).toBe(wrapper.findAll('input[type="radio"]')[0].element)

      await wrapper.findAll('input[type="radio"]')[3].setValue(true)
      await wrapper.get('form').trigger('submit')
      await flushPromises()
      expect(document.activeElement).toBe(wrapper.get('textarea').element)
      expect(wrapper.get('.field-error').attributes('role')).toBe('alert')
    })

    it('loi may chu thi focus khoi thong bao loi cua form', async () => {
      currentUser.value = makeUser('user')
      vi.mocked(createReview).mockRejectedValue(axiosError(500, { message: 'Máy chủ đang bận.' }))
      const wrapper = mountAttached()
      await flushPromises()
      await wrapper.findAll('input[type="radio"]')[3].setValue(true)
      await wrapper.get('textarea').setValue('Ngon, sẽ mua lại lần sau.')
      await wrapper.get('form').trigger('submit')
      await flushPromises()

      const alert = wrapper.get('.form-alert')
      expect(alert.attributes('role')).toBe('alert')
      expect(alert.attributes('tabindex')).toBe('-1')
      expect(document.activeElement).toBe(alert.element)
    })

    it('gui thanh cong thi focus khoi thong bao', async () => {
      currentUser.value = makeUser('user')
      vi.mocked(createReview).mockResolvedValue(myPending)
      const wrapper = mountAttached()
      await flushPromises()
      await wrapper.findAll('input[type="radio"]')[3].setValue(true)
      await wrapper.get('textarea').setValue('Ngon, sẽ mua lại lần sau.')
      await wrapper.get('form').trigger('submit')
      await flushPromises()

      const notice = wrapper.get('.notice')
      expect(notice.attributes('tabindex')).toBe('-1')
      expect(document.activeElement).toBe(notice.element)
    })
  })

})
