// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import {
  listSubjectApplications,
  moderateSubjectApplication,
} from '@/services/subjects'
import AdminSubjectApplicationsView from '@/views/admin/AdminSubjectApplicationsView.vue'

vi.mock('@/services/subjects', () => ({
  listSubjectApplications: vi.fn(),
  moderateSubjectApplication: vi.fn(),
}))

const pendingApplication = {
  id: 1,
  user_id: 3,
  name: 'Hợp tác xã Đà Lạt',
  type: 'cooperative' as const,
  tax_code: 'HTX-001',
  representative: 'Nguyễn Văn A',
  phone: '0912345678',
  email: 'contact@example.com',
  address: 'Phường 8, Đà Lạt',
  district: 'Đà Lạt',
  status: 'pending' as const,
  moderation_note: null,
  created_at: '2026-09-07T00:00:00Z',
  updated_at: '2026-09-07T00:00:00Z',
  applicant: {
    id: 3,
    email: 'user@example.com',
    full_name: 'Nguyễn Văn A',
    role: 'user' as const,
    is_active: true,
  },
}

describe('AdminSubjectApplicationsView', () => {
  it('admin co the mo va xac nhan duyet ho so', async () => {
    vi.mocked(listSubjectApplications).mockResolvedValue({
      items: [pendingApplication],
      page: 1,
      page_size: 10,
      total: 1,
    })
    vi.mocked(moderateSubjectApplication).mockResolvedValue({
      ...pendingApplication,
      status: 'approved',
      moderation_note: null,
      applicant: { ...pendingApplication.applicant, role: 'subject' },
    })

    const wrapper = mount(AdminSubjectApplicationsView)
    await flushPromises()

    expect(wrapper.text()).toContain('Hợp tác xã Đà Lạt')
    const approveButton = wrapper.findAll('button').find((button) => button.text() === 'Duyệt')
    expect(approveButton).toBeDefined()
    await approveButton!.trigger('click')
    await wrapper.get('.moderation-dialog form').trigger('submit')
    await flushPromises()

    expect(moderateSubjectApplication).toHaveBeenCalledWith(1, {
      status: 'approved',
      note: null,
    })
  })
})
