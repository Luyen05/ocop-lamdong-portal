// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

import type { User } from '@/types/auth'

vi.mock('vue-router', () => ({ useRoute: () => ({ query: {} }) }))
vi.mock('@/services/auth', () => ({ getSocialProviders: vi.fn().mockResolvedValue([]) }))

const currentUser = vi.hoisted(() => ({ value: null as unknown }))

vi.mock('@/stores/auth', async () => {
  const { ref: vueRef } = await import('vue')
  const user = vueRef(null)
  currentUser.value = user
  return { authStore: { currentUser: user, updateProfile: vi.fn() } }
})

async function mountWith(user: Partial<User>) {
  const { default: ProfileView } = await import('@/views/ProfileView.vue')
  ;(currentUser.value as ReturnType<typeof ref>).value = {
    id: 1,
    email: 'khach@gmail.com',
    full_name: 'Khách',
    phone: null,
    avatar_url: null,
    is_active: true,
    role: 'user',
    created_at: '2026-10-19T00:00:00Z',
    updated_at: '2026-10-19T00:00:00Z',
    ...user,
  }
  return mount(ProfileView, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
}

describe('ProfileView: cách đăng nhập', () => {
  it('tài khoản tạo bằng Google chưa có mật khẩu', async () => {
    const wrapper = await mountWith({ has_password: false, social_providers: ['google'] })
    expect(wrapper.get('[data-testid="login-methods"]').text()).toBe('Google')
  })

  it('tài khoản có mật khẩu và đã liên kết Facebook', async () => {
    const wrapper = await mountWith({ has_password: true, social_providers: ['facebook'] })
    expect(wrapper.get('[data-testid="login-methods"]').text()).toBe('Email và mật khẩu, Facebook')
  })

  it('dữ liệu cũ chưa có trường mới vẫn hiện mật khẩu', async () => {
    const wrapper = await mountWith({})
    expect(wrapper.get('[data-testid="login-methods"]').text()).toBe('Email và mật khẩu')
  })
})
