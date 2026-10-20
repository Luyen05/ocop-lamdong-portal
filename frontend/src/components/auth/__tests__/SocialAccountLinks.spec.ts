// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

import SocialAccountLinks from '@/components/auth/SocialAccountLinks.vue'
import { getSocialProviders, startSocialLogin, unlinkSocialAccount } from '@/services/auth'
import { authStore } from '@/stores/auth'
import type { User } from '@/types/auth'
import { navigateToExternal } from '@/utils/navigation'
import { clearPendingSocialLogin, readPendingSocialLogin } from '@/utils/social-login'

vi.mock('@/services/auth', () => ({
  getSocialProviders: vi.fn(),
  startSocialLogin: vi.fn(),
  unlinkSocialAccount: vi.fn(),
}))
vi.mock('@/utils/navigation', () => ({ navigateToExternal: vi.fn() }))
vi.mock('@/stores/auth', async () => {
  const { ref: vueRef } = await import('vue')
  return { authStore: { currentUser: vueRef(null), setCurrentUser: vi.fn() } }
})

const currentUser = authStore.currentUser as unknown as ReturnType<typeof ref<Partial<User> | null>>

function setUser(user: Partial<User>): void {
  currentUser.value = { id: 1, role: 'user', has_password: true, social_providers: [], ...user }
}

describe('SocialAccountLinks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    clearPendingSocialLogin()
    vi.mocked(getSocialProviders).mockResolvedValue(['google', 'facebook'])
  })

  it('liên kết: bắt đầu luồng ở chế độ link', async () => {
    setUser({})
    vi.mocked(startSocialLogin).mockResolvedValueOnce('https://www.facebook.com/v26.0/dialog/oauth?x=1')
    const wrapper = mount(SocialAccountLinks)
    await flushPromises()

    const button = wrapper.findAll('button').find((item) => item.text().includes('Facebook'))
    await button!.trigger('click')
    await flushPromises()

    expect(readPendingSocialLogin()?.mode).toBe('link')
    expect(readPendingSocialLogin()?.provider).toBe('facebook')
    expect(navigateToExternal).toHaveBeenCalledWith('https://www.facebook.com/v26.0/dialog/oauth?x=1')
  })

  it('không cho bỏ liên kết cách đăng nhập duy nhất', async () => {
    setUser({ has_password: false, social_providers: ['google'] })
    const wrapper = mount(SocialAccountLinks)
    await flushPromises()

    const unlinkButton = wrapper.findAll('button').find((item) => item.text().includes('Bỏ liên kết'))
    expect(unlinkButton!.attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('cách đăng nhập duy nhất')
  })

  it('bỏ liên kết và cập nhật người dùng', async () => {
    setUser({ social_providers: ['google'] })
    vi.mocked(unlinkSocialAccount).mockResolvedValueOnce({ id: 1, social_providers: [] } as never)
    const wrapper = mount(SocialAccountLinks, { props: { justLinked: 'google' } })
    await flushPromises()
    expect(wrapper.get('[role="status"]').text()).toContain('Đã liên kết Google')

    const unlinkButton = wrapper.findAll('button').find((item) => item.text().includes('Bỏ liên kết'))
    await unlinkButton!.trigger('click')
    await flushPromises()

    expect(unlinkSocialAccount).toHaveBeenCalledWith('google')
    expect(authStore.setCurrentUser).toHaveBeenCalledWith({ id: 1, social_providers: [] })
    expect(wrapper.get('[role="status"]').text()).toContain('Đã bỏ liên kết Google')
  })

  it('ẩn với quản trị viên và khi chưa bật nhà cung cấp nào', async () => {
    setUser({ role: 'admin' })
    const admin = mount(SocialAccountLinks)
    await flushPromises()
    expect(admin.find('[data-testid="social-links"]').exists()).toBe(false)

    setUser({})
    vi.mocked(getSocialProviders).mockResolvedValueOnce([])
    const none = mount(SocialAccountLinks)
    await flushPromises()
    expect(none.find('[data-testid="social-links"]').exists()).toBe(false)
  })
})
