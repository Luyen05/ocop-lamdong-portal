// @vitest-environment jsdom
import { AxiosError, type AxiosAdapter, type InternalAxiosRequestConfig } from 'axios'
import { afterEach, describe, expect, it } from 'vitest'

import http from '@/services/http'
import { AUTH_SESSION_EXPIRED_EVENT, getAccessToken, saveAccessToken } from '@/services/token'

function failWith(status: number, data: unknown): AxiosAdapter {
  return (config: InternalAxiosRequestConfig) =>
    Promise.reject(
      new AxiosError('lỗi', String(status), config, undefined, {
        status,
        statusText: '',
        headers: {},
        config,
        data,
      }),
    )
}

async function reasonFor(status: number, data: unknown): Promise<string | null> {
  let reason: string | null = null
  const listener = (event: Event) => {
    reason = (event as CustomEvent<string>).detail
  }
  window.addEventListener(AUTH_SESSION_EXPIRED_EVENT, listener)
  saveAccessToken('token-cu')
  await http.get('/auth/me', { adapter: failWith(status, data) }).catch(() => undefined)
  window.removeEventListener(AUTH_SESSION_EXPIRED_EVENT, listener)
  return reason
}

describe('http: kết thúc phiên', () => {
  afterEach(() => window.localStorage.clear())

  it('401 thì phiên hết hạn', async () => {
    expect(await reasonFor(401, { code: 'INVALID_TOKEN' })).toBe('expired')
    expect(getAccessToken()).toBeNull()
  })

  it('tài khoản bị khóa thì kết thúc phiên với lý do locked', async () => {
    expect(await reasonFor(403, { code: 'ACCOUNT_INACTIVE' })).toBe('locked')
    expect(getAccessToken()).toBeNull()
  })

  it('403 vì thiếu quyền thì giữ phiên', async () => {
    expect(await reasonFor(403, { code: 'INSUFFICIENT_PERMISSIONS' })).toBeNull()
    expect(getAccessToken()).toBe('token-cu')
  })
})
