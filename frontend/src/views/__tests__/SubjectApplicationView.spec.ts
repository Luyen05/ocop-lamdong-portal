// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import { getMySubjectApplication } from '@/services/subjects'
import { authStore } from '@/stores/auth'
import SubjectApplicationView from '@/views/SubjectApplicationView.vue'

vi.mock('@/services/subjects', () => ({
  createSubjectApplication: vi.fn(),
  getMySubjectApplication: vi.fn(),
  resubmitSubjectApplication: vi.fn(),
}))

vi.mock('@/stores/auth', async () => {
  const { ref } = await import('vue')
  return {
    authStore: {
      currentUser: ref({ id: 3, role: 'user' }),
      refreshUser: vi.fn().mockResolvedValue(undefined),
    },
  }
})

describe('SubjectApplicationView', () => {
  it('hien thi phan hoi va cho phep sua ho so bi tu choi', async () => {
    vi.mocked(getMySubjectApplication).mockResolvedValue({
      id: 1,
      user_id: 3,
      name: 'Hợp tác xã Đà Lạt',
      type: 'cooperative',
      tax_code: 'HTX-001',
      representative: 'Nguyễn Văn A',
      phone: '0912345678',
      email: 'contact@example.com',
      address: 'Phường 8, Đà Lạt',
      district: 'Đà Lạt',
      status: 'rejected',
      moderation_note: 'Cần bổ sung địa chỉ hoạt động.',
      created_at: '2026-09-07T00:00:00Z',
      updated_at: '2026-09-07T00:00:00Z',
    })

    const wrapper = mount(SubjectApplicationView, {
      global: {
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Cần bổ sung')
    expect(wrapper.text()).toContain('Cần bổ sung địa chỉ hoạt động.')
    expect(wrapper.get('button').text()).toContain('Chỉnh sửa hồ sơ')
  })

  it('ho so dang cho duyet: quay lai tab thi cap nhat ngay khi da duoc duyet', async () => {
    const base = {
      id: 2,
      user_id: 3,
      name: 'Vườn dâu Đà Lạt',
      type: 'household' as const,
      tax_code: null,
      representative: 'Trần Thị B',
      phone: '0912345678',
      email: null,
      address: 'Xuân Thọ, Đà Lạt',
      district: 'Xuân Hương - Đà Lạt',
      moderation_note: null,
      created_at: '2026-10-20T00:00:00Z',
      updated_at: '2026-10-20T00:00:00Z',
    }
    vi.mocked(getMySubjectApplication)
      .mockResolvedValueOnce({ ...base, status: 'pending' })
      .mockResolvedValueOnce({ ...base, status: 'approved' })

    const wrapper = mount(SubjectApplicationView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    await flushPromises()
    expect(wrapper.text()).toContain('Đang chờ duyệt')

    window.dispatchEvent(new Event('focus'))
    await flushPromises()

    expect(wrapper.text()).toContain('Đã được duyệt')
    expect(authStore.refreshUser).toHaveBeenCalled()
    wrapper.unmount()
  })
})
