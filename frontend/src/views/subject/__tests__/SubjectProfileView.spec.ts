// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { AxiosError, AxiosHeaders } from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getSubjectProfile, updateSubjectProfile } from '@/services/subjects'
import type { SubjectApplication } from '@/types/subject'
import SubjectProfileView from '@/views/subject/SubjectProfileView.vue'

vi.mock('@/services/subjects', () => ({
  getSubjectProfile: vi.fn(),
  updateSubjectProfile: vi.fn(),
}))

function profile(overrides: Partial<SubjectApplication> = {}): SubjectApplication {
  return {
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
    ...overrides,
  }
}

async function mountView() {
  const wrapper = mount(SubjectProfileView, {
    global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
  })
  await flushPromises()
  return wrapper
}

describe('SubjectProfileView', () => {
  beforeEach(() => {
    vi.mocked(getSubjectProfile).mockReset()
    vi.mocked(updateSubjectProfile).mockReset()
  })

  it('hiển thị hồ sơ; tên, loại hình, mã số thuế chỉ đọc kèm ghi chú liên hệ quản trị viên', async () => {
    vi.mocked(getSubjectProfile).mockResolvedValue(profile())

    const wrapper = await mountView()

    expect(wrapper.text()).toContain('Đã được duyệt')
    const identity = wrapper.get('[data-testid="identity-card"]')
    expect(identity.text()).toContain('Hợp tác xã OCOP Đà Lạt')
    expect(identity.text()).toContain('5800000001')
    expect(identity.text()).toContain('liên hệ quản trị viên')
    expect(identity.find('input').exists()).toBe(false)
    expect(wrapper.find('form').exists()).toBe(false)
  })

  it('sửa thông tin liên hệ và chỉ gửi các trường đã đổi', async () => {
    vi.mocked(getSubjectProfile).mockResolvedValue(profile())
    vi.mocked(updateSubjectProfile).mockResolvedValue(
      profile({ phone: '0909123456', email: null, updated_at: '2026-10-20T08:00:00Z' }),
    )
    const wrapper = await mountView()

    await wrapper.get('[data-testid="edit-contact"]').trigger('click')
    const form = wrapper.get('[data-testid="contact-form"]')
    expect(form.find('#subject-name').exists()).toBe(false)
    expect((form.get('#subject-representative').element as HTMLInputElement).value).toBe('Nguyễn Văn A')
    await form.get('#subject-phone').setValue(' 0909123456 ')
    await form.get('#subject-email').setValue('')
    await form.trigger('submit')
    await flushPromises()

    expect(updateSubjectProfile).toHaveBeenCalledWith({ phone: '0909123456', email: null })
    expect(wrapper.find('[data-testid="contact-form"]').exists()).toBe(false)
    expect(wrapper.get('[role="status"]').text()).toBe('Đã lưu thông tin liên hệ của đơn vị.')
    expect(wrapper.get('[data-testid="contact-card"]').text()).toContain('0909123456')
  })

  it('không đổi gì thì không gọi API', async () => {
    vi.mocked(getSubjectProfile).mockResolvedValue(profile())
    const wrapper = await mountView()

    await wrapper.get('[data-testid="edit-contact"]').trigger('click')
    await wrapper.get('[data-testid="contact-form"]').trigger('submit')

    expect(updateSubjectProfile).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Không có thay đổi nào cần lưu.')
  })

  it('lưu lỗi thì giữ form và hiện thông báo; Hủy khôi phục dữ liệu cũ', async () => {
    vi.mocked(getSubjectProfile).mockResolvedValue(profile())
    vi.mocked(updateSubjectProfile).mockRejectedValue(
      new AxiosError('lỗi', 'ERR_BAD_REQUEST', undefined, undefined, {
        status: 422,
        statusText: '',
        data: { code: 'VALIDATION_ERROR', message: 'Dữ liệu đầu vào không hợp lệ.', details: [] },
        headers: {},
        config: { headers: new AxiosHeaders() },
      }),
    )
    const wrapper = await mountView()

    await wrapper.get('[data-testid="edit-contact"]').trigger('click')
    await wrapper.get('#subject-district').setValue('Bảo Lộc')
    await wrapper.get('[data-testid="contact-form"]').trigger('submit')
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toBe('Dữ liệu đầu vào không hợp lệ.')
    expect(wrapper.find('[data-testid="contact-form"]').exists()).toBe(true)

    const cancel = wrapper.findAll('button').find((button) => button.text() === 'Hủy')
    await cancel!.trigger('click')
    expect(wrapper.get('[data-testid="contact-card"]').text()).toContain('Đà Lạt')
    await wrapper.get('[data-testid="edit-contact"]').trigger('click')
    expect((wrapper.get('#subject-district').element as HTMLInputElement).value).toBe('Đà Lạt')
  })

  it('tải lỗi thì có nút Thử lại', async () => {
    vi.mocked(getSubjectProfile)
      .mockRejectedValueOnce(new Error('mất mạng'))
      .mockResolvedValueOnce(profile())
    const wrapper = await mountView()

    expect(wrapper.text()).toContain('Chưa tải được hồ sơ chủ thể')
    const retry = wrapper.findAll('button').find((button) => button.text().includes('Thử lại'))
    await retry!.trigger('click')
    await flushPromises()

    expect(getSubjectProfile).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('Hợp tác xã OCOP Đà Lạt')
  })
})
