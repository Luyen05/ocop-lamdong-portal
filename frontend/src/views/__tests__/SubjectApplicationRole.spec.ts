// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Ref } from 'vue'

import { getMySubjectApplication } from '@/services/subjects'
import type { User, UserRole } from '@/types/auth'
import type { SubjectApplication, SubjectStatus } from '@/types/subject'
import SubjectApplicationView from '@/views/SubjectApplicationView.vue'

vi.mock('@/services/subjects', () => ({
  createSubjectApplication: vi.fn(),
  getMySubjectApplication: vi.fn(),
  resubmitSubjectApplication: vi.fn(),
}))

const store = vi.hoisted(() => ({ user: null as unknown as Ref<User | null>, refreshUser: vi.fn() }))

vi.mock('@/stores/auth', async () => {
  const { ref } = await import('vue')
  store.user = ref<User | null>(null)
  return { authStore: { currentUser: store.user, refreshUser: store.refreshUser } }
})

function user(role: UserRole): User {
  return {
    id: 3,
    email: 'htx@example.com',
    full_name: 'Nguyễn Văn A',
    phone: null,
    avatar_url: null,
    is_active: true,
    role,
    created_at: '2026-09-07T00:00:00Z',
    updated_at: '2026-09-07T00:00:00Z',
  }
}

function application(status: SubjectStatus): SubjectApplication {
  return {
    id: 1,
    user_id: 3,
    name: 'Hợp tác xã Đà Lạt',
    type: 'cooperative',
    tax_code: null,
    representative: 'Nguyễn Văn A',
    phone: '0912345678',
    email: null,
    address: 'Phường 8, Đà Lạt',
    district: 'Đà Lạt',
    status,
    moderation_note: null,
    created_at: '2026-09-07T00:00:00Z',
    updated_at: '2026-09-07T00:00:00Z',
  }
}

async function mountView() {
  mount(SubjectApplicationView, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
  await flushPromises()
}

describe('SubjectApplicationView: cập nhật vai trò sau khi được duyệt', () => {
  beforeEach(() => {
    store.refreshUser.mockReset()
  })

  it('hồ sơ đã duyệt mà tài khoản còn vai trò user thì tải lại /auth/me', async () => {
    store.user.value = user('user')
    store.refreshUser.mockImplementation(async () => {
      store.user.value = user('subject')
      return store.user.value
    })
    vi.mocked(getMySubjectApplication).mockResolvedValue(application('approved'))

    await mountView()

    expect(store.refreshUser).toHaveBeenCalledOnce()
    expect(store.user.value?.role).toBe('subject')
  })

  it('không tải lại khi vai trò đã đúng hoặc hồ sơ chưa duyệt', async () => {
    store.user.value = user('subject')
    vi.mocked(getMySubjectApplication).mockResolvedValue(application('approved'))
    await mountView()

    store.user.value = user('user')
    vi.mocked(getMySubjectApplication).mockResolvedValue(application('pending'))
    await mountView()

    expect(store.refreshUser).not.toHaveBeenCalled()
  })

  it('tải lại lỗi thì trang vẫn hiển thị bình thường', async () => {
    store.user.value = user('user')
    store.refreshUser.mockRejectedValue(new Error('mất mạng'))
    vi.mocked(getMySubjectApplication).mockResolvedValue(application('approved'))

    const wrapper = mount(SubjectApplicationView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Đã được duyệt')
  })
})
