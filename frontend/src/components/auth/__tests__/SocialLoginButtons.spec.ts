// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import SocialLoginButtons from '@/components/auth/SocialLoginButtons.vue'
import { getSocialProviders, startSocialLogin } from '@/services/auth'
import { navigateToExternal } from '@/utils/navigation'
import { clearPendingSocialLogin, readPendingSocialLogin } from '@/utils/social-login'

vi.mock('@/services/auth', () => ({
  getSocialProviders: vi.fn(),
  startSocialLogin: vi.fn(),
}))

vi.mock('@/utils/navigation', () => ({
  navigateToExternal: vi.fn(),
}))

const getProvidersMock = vi.mocked(getSocialProviders)
const startMock = vi.mocked(startSocialLogin)
const navigateMock = vi.mocked(navigateToExternal)

describe('SocialLoginButtons', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => clearPendingSocialLogin())

  it('ẩn hoàn toàn khi chưa bật nhà cung cấp nào hoặc không tải được danh sách', async () => {
    getProvidersMock.mockResolvedValueOnce([])
    const empty = mount(SocialLoginButtons)
    await flushPromises()
    expect(empty.find('[data-testid="social-login"]').exists()).toBe(false)

    getProvidersMock.mockRejectedValueOnce(new Error('mất mạng'))
    const failed = mount(SocialLoginButtons)
    await flushPromises()
    expect(failed.find('[data-testid="social-login"]').exists()).toBe(false)
  })

  it('chỉ hiện nút của nhà cung cấp đã bật', async () => {
    getProvidersMock.mockResolvedValueOnce(['facebook'])
    const wrapper = mount(SocialLoginButtons)
    await flushPromises()
    const buttons = wrapper.findAll('button')
    expect(buttons).toHaveLength(1)
    expect(buttons[0].text()).toContain('Tiếp tục với Facebook')
  })

  it('Google: gửi state và PKCE, lưu phiên chờ rồi chuyển sang trang Google', async () => {
    getProvidersMock.mockResolvedValueOnce(['google', 'facebook'])
    startMock.mockResolvedValueOnce('https://accounts.google.com/o/oauth2/v2/auth?x=1')
    const wrapper = mount(SocialLoginButtons, { props: { redirect: '/san-pham?q=dau' } })
    await flushPromises()

    await wrapper.findAll('button')[0].trigger('click')
    await flushPromises()

    expect(startMock).toHaveBeenCalledTimes(1)
    const [provider, payload] = startMock.mock.calls[0]
    expect(provider).toBe('google')
    expect(payload.state).toMatch(/^[A-Za-z0-9_-]{43}$/)
    expect(payload.code_challenge).toMatch(/^[A-Za-z0-9_-]{43}$/)

    const pending = readPendingSocialLogin()
    expect(pending?.provider).toBe('google')
    expect(pending?.mode).toBe('login')
    expect(pending?.state).toBe(payload.state)
    expect(pending?.codeVerifier).toMatch(/^[A-Za-z0-9_-]{64}$/)
    expect(pending?.redirect).toBe('/san-pham?q=dau')
    expect(navigateMock).toHaveBeenCalledWith('https://accounts.google.com/o/oauth2/v2/auth?x=1')
  })

  it('Facebook: không gửi PKCE; báo lỗi và cho bấm lại khi không mở được trang', async () => {
    getProvidersMock.mockResolvedValueOnce(['facebook'])
    startMock.mockRejectedValueOnce(new Error('lỗi'))
    const wrapper = mount(SocialLoginButtons, { props: { redirect: '//trang-la' } })
    await flushPromises()

    await wrapper.get('button').trigger('click')
    await flushPromises()

    expect(startMock.mock.calls[0][1]).not.toHaveProperty('code_challenge')
    expect(wrapper.get('[role="alert"]').text()).toContain('Chưa mở được trang đăng nhập Facebook')
    expect(wrapper.get('button').attributes('disabled')).toBeUndefined()
    expect(navigateMock).not.toHaveBeenCalled()
    expect(readPendingSocialLogin()).toBeNull()
  })
})
