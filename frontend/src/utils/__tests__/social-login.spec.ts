// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest'

import {
  base64UrlEncode,
  clearPendingSocialLogin,
  pkceChallenge,
  randomUrlSafeString,
  readPendingSocialLogin,
  safeRedirect,
  savePendingSocialLogin,
} from '@/utils/social-login'

describe('PKCE', () => {
  it('tính code_challenge đúng ví dụ trong RFC 7636', async () => {
    await expect(pkceChallenge('dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk')).resolves.toBe(
      'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM',
    )
  })

  it('sinh chuỗi ngẫu nhiên dạng base64url, không trùng nhau', () => {
    const first = randomUrlSafeString(32)
    expect(first).toMatch(/^[A-Za-z0-9_-]{43}$/)
    expect(randomUrlSafeString(32)).not.toBe(first)
    expect(base64UrlEncode(new Uint8Array([251, 255]))).toBe('-_8')
  })
})

describe('phiên đăng nhập đang chờ', () => {
  afterEach(() => clearPendingSocialLogin())

  it('lưu, đọc và xóa', () => {
    savePendingSocialLogin({
      provider: 'google',
      mode: 'link',
      state: 'abc',
      codeVerifier: 'xyz',
      redirect: '/san-pham',
      createdAt: 1_000,
    })
    expect(readPendingSocialLogin(2_000)).toEqual({
      provider: 'google',
      mode: 'link',
      state: 'abc',
      codeVerifier: 'xyz',
      redirect: '/san-pham',
      createdAt: 1_000,
    })
    clearPendingSocialLogin()
    expect(readPendingSocialLogin(2_000)).toBeNull()
  })

  it('bỏ phiên quá 10 phút và đường dẫn chuyển hướng ra ngoài', () => {
    savePendingSocialLogin({
      provider: 'facebook',
      mode: 'login',
      state: 'abc',
      codeVerifier: null,
      redirect: '//trang-la.example',
      createdAt: 0,
    })
    expect(readPendingSocialLogin(60_000)?.redirect).toBeNull()
    expect(readPendingSocialLogin(10 * 60 * 1000 + 1)).toBeNull()
  })

  it('bỏ dữ liệu hỏng', () => {
    window.sessionStorage.setItem('ocop_social_login', '{khong-phai-json')
    expect(readPendingSocialLogin()).toBeNull()
    window.sessionStorage.setItem('ocop_social_login', JSON.stringify({ provider: 'github', state: 'a', createdAt: 0 }))
    expect(readPendingSocialLogin(1)).toBeNull()
  })

  it('chỉ nhận đường dẫn nội bộ', () => {
    expect(safeRedirect('/tai-khoan')).toBe('/tai-khoan')
    expect(safeRedirect('//evil.example')).toBeNull()
    expect(safeRedirect('https://evil.example')).toBeNull()
    expect(safeRedirect(['/a'])).toBeNull()
  })
})
