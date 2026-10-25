// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { completeSocialLogin, linkSocialAccount } from '@/services/auth'
import { authStore } from '@/stores/auth'
import { clearPendingSocialLogin, readPendingSocialLogin, savePendingSocialLogin } from '@/utils/social-login'
import SocialLoginCallbackView from '@/views/SocialLoginCallbackView.vue'

const routeState = vi.hoisted(() => ({
  path: '/dang-nhap/mang-xa-hoi/google',
  params: { provider: 'google' } as Record<string, string>,
  query: {} as Record<string, string>,
}))
const replaceMock = vi.hoisted(() => vi.fn())

vi.mock('vue-router', () => ({
  useRoute: () => routeState,
  useRouter: () => ({ replace: replaceMock }),
}))

vi.mock('@/services/auth', () => ({
  completeSocialLogin: vi.fn(),
  linkSocialAccount: vi.fn(),
}))

const authState = vi.hoisted(() => ({ isAuthenticated: { value: false } }))
vi.mock('@/stores/auth', () => ({
  authStore: {
    loginWithToken: vi.fn(),
    setCurrentUser: vi.fn(),
    isAuthenticated: authState.isAuthenticated,
  },
}))

const completeMock = vi.mocked(completeSocialLogin)
const loginWithTokenMock = vi.mocked(authStore.loginWithToken)
const linkMock = vi.mocked(linkSocialAccount)
const setUserMock = vi.mocked(authStore.setCurrentUser)

const globalOptions = {
  stubs: {
    AuthLayout: { props: ['title'], template: '<div><h2>{{ title }}</h2><slot /></div>' },
    RouterLink: { props: ['to'], template: '<a :data-to="JSON.stringify(to)"><slot /></a>' },
  },
}

function savePending(overrides: Partial<Parameters<typeof savePendingSocialLogin>[0]> = {}): void {
  savePendingSocialLogin({
    provider: 'google',
    mode: 'login',
    state: 'state-1',
    codeVerifier: 'verifier-1',
    redirect: '/san-pham',
    createdAt: Date.now(),
    ...overrides,
  })
}

describe('SocialLoginCallbackView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    routeState.params = { provider: 'google' }
    routeState.query = { code: 'ma-google', state: 'state-1' }
    authState.isAuthenticated.value = false
  })

  afterEach(() => clearPendingSocialLogin())

  it('đổi mã, lưu đăng nhập và mở lại trang người dùng đang xem', async () => {
    savePending()
    completeMock.mockResolvedValueOnce({
      access_token: 'jwt',
      token_type: 'bearer',
      expires_in: 3600,
      is_new_user: true,
    })
    loginWithTokenMock.mockResolvedValueOnce({ role: 'user' } as never)

    const wrapper = mount(SocialLoginCallbackView, { global: globalOptions })
    expect(wrapper.get('[role="status"]').text()).toContain('Đang hoàn tất với Google')
    await flushPromises()

    expect(completeMock).toHaveBeenCalledWith('google', { code: 'ma-google', code_verifier: 'verifier-1' })
    expect(loginWithTokenMock).toHaveBeenCalledWith('jwt')
    // Mã bị xóa khỏi thanh địa chỉ trước, rồi mới chuyển trang.
    expect(replaceMock).toHaveBeenNthCalledWith(1, { path: '/dang-nhap/mang-xa-hoi/google', query: {} })
    expect(replaceMock).toHaveBeenLastCalledWith('/san-pham')
    // Phiên chờ bị xóa ngay để tải lại trang không gửi lại mã đã dùng.
    expect(readPendingSocialLogin()).toBeNull()
  })

  it('chủ thể đăng nhập bằng Facebook không có trang chờ thì về khu chủ thể', async () => {
    routeState.params = { provider: 'facebook' }
    savePending({ provider: 'facebook', codeVerifier: null, redirect: null })
    completeMock.mockResolvedValueOnce({
      access_token: 'jwt',
      token_type: 'bearer',
      expires_in: 3600,
      is_new_user: false,
    })
    loginWithTokenMock.mockResolvedValueOnce({ role: 'subject' } as never)

    mount(SocialLoginCallbackView, { global: globalOptions })
    await flushPromises()

    expect(completeMock).toHaveBeenCalledWith('facebook', { code: 'ma-google' })
    expect(replaceMock).toHaveBeenLastCalledWith('/chu-the/san-pham')
  })

  it('state không khớp thì không gửi mã lên máy chủ', async () => {
    savePending({ state: 'state-khac' })
    const wrapper = mount(SocialLoginCallbackView, { global: globalOptions })
    await flushPromises()

    expect(completeMock).not.toHaveBeenCalled()
    expect(wrapper.get('[role="alert"]').text()).toContain('Phiên đăng nhập không hợp lệ')
    expect(wrapper.text()).toContain('Thử lại')
  })

  it('không có phiên chờ (mở thẳng đường dẫn) cũng bị từ chối', async () => {
    mount(SocialLoginCallbackView, { global: globalOptions })
    await flushPromises()
    expect(completeMock).not.toHaveBeenCalled()
  })

  it('người dùng hủy trên trang Google', async () => {
    savePending()
    routeState.query = { error: 'access_denied', state: 'state-1' }
    const wrapper = mount(SocialLoginCallbackView, { global: globalOptions })
    await flushPromises()

    expect(completeMock).not.toHaveBeenCalled()
    expect(wrapper.get('[role="alert"]').text()).toContain('Bạn đã hủy hoặc chưa cho phép đăng nhập bằng Google')
    expect(wrapper.find('[data-to]').attributes('data-to')).toContain('/san-pham')
  })

  it('hiện thông báo lỗi của máy chủ', async () => {
    savePending()
    completeMock.mockRejectedValueOnce({
      isAxiosError: true,
      response: {
        status: 409,
        data: { message: 'Email này thuộc tài khoản chủ thể hoặc quản trị.' },
      },
    })
    const wrapper = mount(SocialLoginCallbackView, { global: globalOptions })
    await flushPromises()

    expect(loginWithTokenMock).not.toHaveBeenCalled()
    expect(wrapper.get('[role="alert"]').text()).toContain('Email này thuộc tài khoản chủ thể hoặc quản trị.')
  })

  it('liên kết: người dùng đang đăng nhập thêm Google rồi về trang tài khoản', async () => {
    authState.isAuthenticated.value = true
    savePending({ mode: 'link', redirect: null })
    linkMock.mockResolvedValueOnce({ id: 7, social_providers: ['google'] } as never)

    const wrapper = mount(SocialLoginCallbackView, { global: globalOptions })
    expect(wrapper.text()).toContain('Liên kết Google')
    await flushPromises()

    expect(linkMock).toHaveBeenCalledWith('google', { code: 'ma-google', code_verifier: 'verifier-1' })
    expect(completeMock).not.toHaveBeenCalled()
    expect(setUserMock).toHaveBeenCalledWith({ id: 7, social_providers: ['google'] })
    expect(replaceMock).toHaveBeenLastCalledWith({ path: '/tai-khoan', query: { 'lien-ket': 'google' } })
  })

  it('liên kết khi phiên đăng nhập đã mất thì báo cần đăng nhập', async () => {
    savePending({ mode: 'link' })
    const wrapper = mount(SocialLoginCallbackView, { global: globalOptions })
    await flushPromises()

    expect(linkMock).not.toHaveBeenCalled()
    expect(wrapper.get('[role="alert"]').text()).toContain('Bạn cần đăng nhập trước khi liên kết Google')
    expect(wrapper.find('[data-to]').attributes('data-to')).toContain('/tai-khoan')
  })

  it('liên kết bị từ chối thì hiện lý do của máy chủ', async () => {
    authState.isAuthenticated.value = true
    savePending({ mode: 'link' })
    linkMock.mockRejectedValueOnce({
      isAxiosError: true,
      response: { status: 409, data: { message: 'Tài khoản Google này đã liên kết với một tài khoản khác trên cổng.' } },
    })
    const wrapper = mount(SocialLoginCallbackView, { global: globalOptions })
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('đã liên kết với một tài khoản khác')
  })
})
