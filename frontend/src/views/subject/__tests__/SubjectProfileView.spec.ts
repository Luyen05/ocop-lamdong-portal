// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import { getMySubjectApplication } from '@/services/subjects'
import SubjectProfileView from '@/views/subject/SubjectProfileView.vue'

vi.mock('@/services/subjects', () => ({
  getMySubjectApplication: vi.fn(),
}))

describe('SubjectProfileView', () => {
  it('hien thi ho so da duyet o che do chi doc', async () => {
    vi.mocked(getMySubjectApplication).mockResolvedValue({
      id: 1,
      user_id: 2,
      name: 'Hợp tác xã OCOP Đà Lạt',
      type: 'cooperative',
      tax_code: '5800000001',
      representative: 'Nguyễn Văn A',
      phone: '0912345678',
      email: 'contact@example.com',
      address: 'Phường Xuân Hương - Đà Lạt',
      district: 'Đà Lạt',
      status: 'approved',
      moderation_note: 'Hồ sơ hợp lệ.',
      created_at: '2026-09-01T00:00:00Z',
      updated_at: '2026-09-10T08:00:00Z',
    })

    const wrapper = mount(SubjectProfileView, {
      global: {
        stubs: { RouterLink: { template: '<a><slot /></a>' } },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Đã được duyệt')
    expect(wrapper.text()).toContain('Hợp tác xã OCOP Đà Lạt')
    expect(wrapper.text()).toContain('Hồ sơ đã duyệt chỉ được xem')
    expect(wrapper.find('input').exists()).toBe(false)
  })
})
