// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { AxiosError, AxiosHeaders } from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Ref } from 'vue'

import type { User } from '@/types/auth'

vi.mock('vue-router', () => ({ useRoute: () => ({ query: {} }) }))

const mocks = vi.hoisted(() => ({
  changePassword: vi.fn(),
  refreshUser: vi.fn(),
  user: null as unknown as Ref<User | null>,
}))

vi.mock('@/services/auth', () => ({
  getSocialProviders: vi.fn().mockResolvedValue([]),
  changePassword: mocks.changePassword,
}))

vi.mock('@/stores/auth', async () => {
  const { ref } = await import('vue')
  mocks.user = ref<User | null>(null)
  return {
    authStore: { currentUser: mocks.user, updateProfile: vi.fn(), refreshUser: mocks.refreshUser, setCurrentUser: vi.fn() },
  }
})

function makeUser(overrides: Partial<User> = {}): User {
  return {
    id: 1,
    email: 'khach@gmail.com',
    full_name: 'Khách',
    phone: null,
    avatar_url: null,
    is_active: true,
    role: 'user',
    has_password: true,
    social_providers: [],
    created_at: '2026-10-19T00:00:00Z',
    updated_at: '2026-10-19T00:00:00Z',
    ...overrides,
  }
}

async function mountProfile(user: User) {
  const { default: ProfileView } = await import('@/views/ProfileView.vue')
  mocks.user.value = user
  const wrapper = mount(ProfileView, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
  await flushPromises()
  return wrapper
}

function apiError(status: number, message: string): AxiosError {
  return new AxiosError('lỗi', 'ERR_BAD_REQUEST', undefined, undefined, {
    status,
    statusText: '',
    data: { code: 'INVALID_CURRENT_PASSWORD', message, details: null },
    headers: {},
    config: { headers: new AxiosHeaders() },
  })
}

describe('ProfileView: khung mật khẩu', () => {
  beforeEach(() => {
    mocks.changePassword.mockReset()
    mocks.refreshUser.mockReset()
  })

  it('tài khoản có mật khẩu: đổi mật khẩu cần mật khẩu hiện tại rồi tải lại người dùng', async () => {
    mocks.changePassword.mockResolvedValue(undefined)
    mocks.refreshUser.mockResolvedValue(makeUser())
    const wrapper = await mountProfile(makeUser())
    const section = wrapper.get('[data-testid="password-settings"]')

    expect(section.get('h2').text()).toBe('Mật khẩu')
    await section.get('#current-password').setValue('MatKhauCu123')
    await section.get('#new-password').setValue('MatKhauMoi456!')
    await section.get('#new-password-confirmation').setValue('MatKhauMoi456!')
    expect(section.get('#new-password-strength').text()).toContain('Tốt')
    await section.get('form').trigger('submit')
    await flushPromises()

    expect(mocks.changePassword).toHaveBeenCalledWith({
      current_password: 'MatKhauCu123',
      new_password: 'MatKhauMoi456!',
    })
    expect(mocks.refreshUser).toHaveBeenCalledOnce()
    expect(section.get('[role="status"]').text()).toBe('Đã đổi mật khẩu.')
    expect((section.get('#new-password').element as HTMLInputElement).value).toBe('')
  })

  it('tài khoản Google chưa có mật khẩu: đặt mật khẩu, không hỏi mật khẩu hiện tại', async () => {
    mocks.changePassword.mockResolvedValue(undefined)
    mocks.refreshUser.mockImplementation(async () => {
      mocks.user.value = makeUser({ has_password: true, social_providers: ['google'] })
      return mocks.user.value
    })
    const wrapper = await mountProfile(makeUser({ has_password: false, social_providers: ['google'] }))
    const section = wrapper.get('[data-testid="password-settings"]')

    expect(section.get('h2').text()).toBe('Đặt mật khẩu')
    expect(section.find('#current-password').exists()).toBe(false)
    await section.get('#new-password').setValue('MatKhauMoi456')
    await section.get('#new-password-confirmation').setValue('MatKhauMoi456')
    await section.get('form').trigger('submit')
    await flushPromises()

    expect(mocks.changePassword).toHaveBeenCalledWith({ new_password: 'MatKhauMoi456' })
    expect(wrapper.get('[data-testid="login-methods"]').text()).toBe('Email và mật khẩu, Google')
    expect(wrapper.get('[data-testid="password-settings"] h2').text()).toBe('Mật khẩu')
    expect(wrapper.get('[data-testid="password-settings"] [role="status"]').text()).toContain('Đã đặt mật khẩu')
  })

  it('báo lỗi khi nhập lại không khớp hoặc mật khẩu quá ngắn, không gọi API', async () => {
    const wrapper = await mountProfile(makeUser())
    const section = wrapper.get('[data-testid="password-settings"]')

    await section.get('#current-password').setValue('MatKhauCu123')
    await section.get('#new-password').setValue('MatKhauMoi456')
    await section.get('#new-password-confirmation').setValue('MatKhauKhac789')
    expect(section.get('#new-password-confirmation').attributes('aria-invalid')).toBe('true')
    await section.get('form').trigger('submit')
    expect(section.get('[role="alert"]').text()).toBe('Mật khẩu nhập lại chưa khớp.')

    await section.get('#new-password').setValue('ngan')
    await section.get('#new-password-confirmation').setValue('ngan')
    await section.get('form').trigger('submit')
    expect(section.get('[role="alert"]').text()).toContain('ít nhất 8 ký tự')
    expect(mocks.changePassword).not.toHaveBeenCalled()
  })

  it('hiện lỗi từ máy chủ khi mật khẩu hiện tại sai', async () => {
    mocks.changePassword.mockRejectedValue(apiError(400, 'Mật khẩu hiện tại không đúng.'))
    const wrapper = await mountProfile(makeUser())
    const section = wrapper.get('[data-testid="password-settings"]')

    await section.get('#current-password').setValue('Sai')
    await section.get('#new-password').setValue('MatKhauMoi456')
    await section.get('#new-password-confirmation').setValue('MatKhauMoi456')
    await section.get('form').trigger('submit')
    await flushPromises()

    expect(section.get('[role="alert"]').text()).toBe('Mật khẩu hiện tại không đúng.')
    expect(mocks.refreshUser).not.toHaveBeenCalled()
  })

  it('nút hiện/ẩn mật khẩu đổi kiểu ô nhập và có nhãn', async () => {
    const wrapper = await mountProfile(makeUser())
    const toggle = wrapper.get('button[aria-label="Hiện mật khẩu mới"]')

    await toggle.trigger('click')

    expect(wrapper.get('#new-password').attributes('type')).toBe('text')
    expect(toggle.attributes('aria-pressed')).toBe('true')
    expect(toggle.attributes('aria-label')).toBe('Ẩn mật khẩu mới')
  })
})
