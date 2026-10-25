// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { listAdminUsers, updateAdminUserStatus } from '@/services/admin-users'
import type { AdminUser, AdminUserListResponse } from '@/types/admin-user'
import AdminUsersView from '@/views/admin/AdminUsersView.vue'

vi.mock('@/services/admin-users', () => ({
  listAdminUsers: vi.fn(),
  updateAdminUserStatus: vi.fn(),
}))
vi.mock('@/stores/auth', () => ({
  authStore: { currentUser: { value: { id: 1, full_name: 'Quản trị chính' } } },
}))

const adminSelf: AdminUser = {
  id: 1,
  email: 'admin@example.com',
  full_name: 'Quản trị chính',
  phone: null,
  role: 'admin',
  is_active: true,
  created_at: '2026-09-01T00:00:00Z',
  has_password: true,
  social_providers: [],
  subject: null,
}

const subjectUser: AdminUser = {
  id: 3,
  email: 'htx@example.com',
  full_name: 'Chủ HTX Cầu Đất',
  phone: '0912345678',
  role: 'subject',
  is_active: true,
  created_at: '2026-09-03T00:00:00Z',
  has_password: true,
  social_providers: ['google'],
  subject: { id: 1, name: 'HTX Chè Cầu Đất', status: 'approved' },
}

function listResponse(items: AdminUser[]): AdminUserListResponse {
  return { items, page: 1, page_size: 20, total: items.length }
}

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((done) => {
    resolve = done
  })
  return { promise, resolve }
}

describe('AdminUsersView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(listAdminUsers).mockResolvedValue(listResponse([subjectUser, adminSelf]))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('hiện thông tin tài khoản và không có nút khóa với chính mình', async () => {
    const wrapper = mount(AdminUsersView)
    await flushPromises()

    expect(wrapper.text()).toContain('HTX Chè Cầu Đất · hồ sơ đã duyệt')
    expect(wrapper.text()).toContain('Mật khẩu, Google')
    expect(wrapper.text()).toContain('Tài khoản của bạn')
    const lockButtons = wrapper.findAll('button').filter((button) => button.text().includes('Khóa'))
    expect(lockButtons).toHaveLength(1)
    expect(lockButtons[0].attributes('aria-label')).toBe('Khóa tài khoản htx@example.com')
  })

  it('khóa tài khoản sau khi xác nhận trong hộp thoại', async () => {
    vi.mocked(updateAdminUserStatus).mockResolvedValue({ ...subjectUser, is_active: false })
    const wrapper = mount(AdminUsersView, { attachTo: document.body })
    await flushPromises()

    await wrapper.get('button[aria-label="Khóa tài khoản htx@example.com"]').trigger('click')
    const dialog = wrapper.get('[role="alertdialog"]')
    expect(dialog.text()).toContain('Sản phẩm và điểm du lịch của chủ thể này sẽ tạm ngừng hiển thị')
    expect(updateAdminUserStatus).not.toHaveBeenCalled()

    const confirm = dialog.findAll('button').find((button) => button.text() === 'Xác nhận khóa')
    await confirm!.trigger('click')
    await flushPromises()

    expect(updateAdminUserStatus).toHaveBeenCalledWith(3, false)
    expect(wrapper.find('[role="alertdialog"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Đã khóa tài khoản htx@example.com.')
    expect(wrapper.get('button[aria-label="Mở khóa tài khoản htx@example.com"]').text()).toContain('Mở khóa')
    wrapper.unmount()
  })

  it('báo lỗi trong hộp thoại khi máy chủ từ chối', async () => {
    vi.mocked(updateAdminUserStatus).mockRejectedValue(new Error('boom'))
    const wrapper = mount(AdminUsersView)
    await flushPromises()

    await wrapper.get('button[aria-label="Khóa tài khoản htx@example.com"]').trigger('click')
    const confirm = wrapper.findAll('[role="alertdialog"] button').find((button) => button.text() === 'Xác nhận khóa')
    await confirm!.trigger('click')
    await flushPromises()

    expect(wrapper.get('[role="alertdialog"] [role="alert"]').text()).toBe('Không thể cập nhật trạng thái tài khoản.')
  })

  it('tìm kiếm có debounce và bỏ kết quả cũ khi lọc nhanh', async () => {
    vi.useFakeTimers()
    const wrapper = mount(AdminUsersView)
    await flushPromises()
    expect(listAdminUsers).toHaveBeenCalledTimes(1)

    const slow = deferred<AdminUserListResponse>()
    const fast = deferred<AdminUserListResponse>()
    vi.mocked(listAdminUsers).mockReturnValueOnce(slow.promise).mockReturnValueOnce(fast.promise)

    await wrapper.get('input[type="search"]').setValue('h')
    await wrapper.get('input[type="search"]').setValue('htx')
    vi.advanceTimersByTime(349)
    expect(listAdminUsers).toHaveBeenCalledTimes(1)
    vi.advanceTimersByTime(1)
    expect(listAdminUsers).toHaveBeenCalledTimes(2)
    expect(listAdminUsers).toHaveBeenLastCalledWith(
      expect.objectContaining({ q: 'htx', page: 1, role: undefined, is_active: undefined }),
    )

    const roleSelect = wrapper.findAll('select')[0]
    await roleSelect.setValue('admin')
    expect(listAdminUsers).toHaveBeenCalledTimes(3)
    expect(listAdminUsers).toHaveBeenLastCalledWith(expect.objectContaining({ q: 'htx', role: 'admin' }))

    fast.resolve(listResponse([adminSelf]))
    await flushPromises()
    slow.resolve(listResponse([subjectUser]))
    await flushPromises()

    expect(wrapper.text()).toContain('Quản trị chính')
    expect(wrapper.text()).not.toContain('Chủ HTX Cầu Đất')
  })

  it('lọc trạng thái gửi is_active và có trạng thái rỗng, lỗi', async () => {
    const wrapper = mount(AdminUsersView)
    await flushPromises()

    vi.mocked(listAdminUsers).mockResolvedValueOnce(listResponse([]))
    await wrapper.findAll('select')[1].setValue('locked')
    await flushPromises()
    expect(listAdminUsers).toHaveBeenLastCalledWith(expect.objectContaining({ is_active: false }))
    expect(wrapper.text()).toContain('Không có tài khoản phù hợp')

    vi.mocked(listAdminUsers).mockRejectedValueOnce(new Error('offline'))
    await wrapper.findAll('select')[1].setValue('active')
    await flushPromises()
    expect(wrapper.text()).toContain('Không thể tải danh sách người dùng.')

    await wrapper.findAll('button').find((button) => button.text().includes('Thử lại'))!.trigger('click')
    await flushPromises()
    expect(listAdminUsers).toHaveBeenLastCalledWith(expect.objectContaining({ is_active: true }))
    expect(wrapper.text()).toContain('Chủ HTX Cầu Đất')
  })
})
