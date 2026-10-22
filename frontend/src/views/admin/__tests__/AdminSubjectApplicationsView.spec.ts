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

  it('loc nhanh lien tiep chi hien ket qua cua lan tai moi nhat', async () => {
    const page = (name: string) => ({
      items: [{ ...pendingApplication, id: name.length, name }],
      page: 1,
      page_size: 10,
      total: 1,
    })
    let resolveSlow!: (value: ReturnType<typeof page>) => void
    vi.mocked(listSubjectApplications)
      .mockReset()
      .mockResolvedValueOnce(page('Ban đầu'))
      .mockImplementationOnce(() => new Promise((resolve) => { resolveSlow = resolve }))
      .mockResolvedValueOnce(page('Kết quả mới nhất'))

    const wrapper = mount(AdminSubjectApplicationsView)
    await flushPromises()
    await wrapper.get('form.filter-bar').trigger('submit')
    await wrapper.get('form.filter-bar').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('Kết quả mới nhất')

    resolveSlow(page('Kết quả cũ trả về muộn'))
    await flushPromises()

    expect(wrapper.text()).toContain('Kết quả mới nhất')
    expect(wrapper.text()).not.toContain('Kết quả cũ trả về muộn')
  })

  it('hien thong bao thanh cong role=status sau khi duyet va sau khi tu choi (C12)', async () => {
    vi.mocked(listSubjectApplications).mockReset().mockResolvedValue({
      items: [pendingApplication],
      page: 1,
      page_size: 10,
      total: 1,
    })
    vi.mocked(moderateSubjectApplication).mockResolvedValue({ ...pendingApplication, status: 'approved' })

    const wrapper = mount(AdminSubjectApplicationsView)
    await flushPromises()
    expect(wrapper.find('[role="status"]').exists()).toBe(false)

    await wrapper.findAll('button').find((button) => button.text() === 'Duyệt')!.trigger('click')
    await wrapper.get('.moderation-dialog form').trigger('submit')
    await flushPromises()
    const status = wrapper.get('.alert-success[role="status"]')
    expect(status.text()).toContain('Đã duyệt hồ sơ “Hợp tác xã Đà Lạt”')

    await wrapper.findAll('button').find((button) => button.text() === 'Từ chối')!.trigger('click')
    expect(wrapper.get('.reject-hint').text()).toContain('Cần bổ sung')
    await wrapper.get('.moderation-dialog textarea').setValue('Thiếu giấy phép')
    await wrapper.get('.moderation-dialog form').trigger('submit')
    await flushPromises()
    expect(wrapper.get('.alert-success[role="status"]').text()).toContain('Cần bổ sung')
  })

  it('bang co th scope va moi o co data-label de chuyen thanh the tren dien thoai (B18)', async () => {
    vi.mocked(listSubjectApplications).mockReset().mockResolvedValue({
      items: [pendingApplication, { ...pendingApplication, id: 2, status: 'rejected' as const }],
      page: 1,
      page_size: 10,
      total: 2,
    })
    const wrapper = mount(AdminSubjectApplicationsView)
    await flushPromises()

    const headers = wrapper.findAll('thead th')
    expect(headers).toHaveLength(6)
    expect(headers.every((header) => header.attributes('scope') === 'col')).toBe(true)
    const cells = wrapper.findAll('tbody tr')[0].findAll('td')
    expect(cells.map((cell) => cell.attributes('data-label'))).toEqual([
      'Đơn vị',
      'Người đăng ký',
      'Khu vực',
      'Ngày gửi',
      'Trạng thái',
      'Thao tác',
    ])
    // Hai phía dùng cùng một cách gọi cho hồ sơ bị từ chối.
    expect(wrapper.findAll('.status-badge')[1].text()).toBe('Cần bổ sung')
  })
})
