// @vitest-environment jsdom
import { AxiosError, AxiosHeaders } from 'axios'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/services/auth', () => ({
  getMe: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
  updateMe: vi.fn(),
}))

function httpError(status?: number): AxiosError {
  const response = status
    ? { status, statusText: '', data: {}, headers: {}, config: { headers: new AxiosHeaders() } }
    : undefined
  return new AxiosError('lỗi', status ? 'ERR_BAD_RESPONSE' : 'ERR_NETWORK', undefined, undefined, response)
}

async function freshStore() {
  vi.resetModules()
  window.localStorage.setItem('ocop_access_token', 'token-cu')
  const authService = await import('@/services/auth')
  const { authStore } = await import('@/stores/auth')
  return { authService: vi.mocked(authService), authStore }
}

describe('authStore.initialize', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('xóa phiên khi máy chủ từ chối token (401)', async () => {
    const { authService, authStore } = await freshStore()
    authService.getMe.mockRejectedValueOnce(httpError(401))
    await authStore.initialize()
    expect(window.localStorage.getItem('ocop_access_token')).toBeNull()
  })

  it('giữ token khi mất mạng và thử lại ở lần sau', async () => {
    const { authService, authStore } = await freshStore()
    authService.getMe.mockRejectedValueOnce(httpError())
    await authStore.initialize()
    expect(window.localStorage.getItem('ocop_access_token')).toBe('token-cu')

    authService.getMe.mockResolvedValueOnce({ id: 1, email: 'a@b.vn', full_name: 'A', role: 'user' } as never)
    await authStore.initialize()
    expect(authStore.currentUser.value?.id).toBe(1)
    expect(authService.getMe).toHaveBeenCalledTimes(2)
  })
})
