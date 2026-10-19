import { startSocialLogin } from '@/services/auth'
import { navigateToExternal } from '@/utils/navigation'
import type { SocialProvider } from '@/types/auth'

/**
 * Hỗ trợ đăng nhập Google/Facebook (OAuth 2.0 authorization code).
 *
 * - `state`: chuỗi ngẫu nhiên gửi đi và nhận lại khi Google/Facebook trả người dùng về,
 *   so khớp để chặn yêu cầu giả mạo.
 * - PKCE (Google): `code_verifier` giữ ở trình duyệt, chỉ gửi `code_challenge` = base64url(SHA-256(verifier)).
 * Hai giá trị được giữ trong sessionStorage của tab hiện tại trong 10 phút.
 */

export const SOCIAL_PROVIDER_LABELS: Record<SocialProvider, string> = {
  google: 'Google',
  facebook: 'Facebook',
}

const PENDING_KEY = 'ocop_social_login'
const PENDING_TTL_MS = 10 * 60 * 1000

/** login: đăng nhập/đăng ký; link: người dùng đang đăng nhập liên kết thêm tài khoản. */
export type SocialLoginMode = 'login' | 'link'

export interface PendingSocialLogin {
  provider: SocialProvider
  mode: SocialLoginMode
  state: string
  codeVerifier: string | null
  redirect: string | null
  createdAt: number
}

export function isSocialProvider(value: unknown): value is SocialProvider {
  return value === 'google' || value === 'facebook'
}

export function base64UrlEncode(bytes: Uint8Array): string {
  let binary = ''
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte)
  })
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

/** Chuỗi ngẫu nhiên an toàn dạng base64url (32 byte cho ra 43 ký tự). */
export function randomUrlSafeString(byteLength = 32): string {
  const bytes = new Uint8Array(byteLength)
  globalThis.crypto.getRandomValues(bytes)
  return base64UrlEncode(bytes)
}

export async function pkceChallenge(codeVerifier: string): Promise<string> {
  const digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(codeVerifier))
  return base64UrlEncode(new Uint8Array(digest))
}

/** Chỉ nhận đường dẫn nội bộ ("/san-pham"), không nhận "//tên-miền-khác" hay địa chỉ đầy đủ. */
export function safeRedirect(value: unknown): string | null {
  return typeof value === 'string' && value.startsWith('/') && !value.startsWith('//') ? value : null
}

export function savePendingSocialLogin(pending: PendingSocialLogin): void {
  try {
    window.sessionStorage.setItem(PENDING_KEY, JSON.stringify(pending))
  } catch {
    // Trình duyệt chặn sessionStorage: trang trả về sẽ báo phiên không hợp lệ.
  }
}

export function readPendingSocialLogin(now = Date.now()): PendingSocialLogin | null {
  let raw: string | null = null
  try {
    raw = window.sessionStorage.getItem(PENDING_KEY)
  } catch {
    return null
  }
  if (!raw) return null
  try {
    const value = JSON.parse(raw) as Partial<PendingSocialLogin>
    if (
      !isSocialProvider(value.provider)
      || typeof value.state !== 'string'
      || typeof value.createdAt !== 'number'
      || now - value.createdAt > PENDING_TTL_MS
      || value.createdAt > now + 60_000
    ) {
      return null
    }
    return {
      provider: value.provider,
      mode: value.mode === 'link' ? 'link' : 'login',
      state: value.state,
      codeVerifier: typeof value.codeVerifier === 'string' ? value.codeVerifier : null,
      redirect: safeRedirect(value.redirect),
      createdAt: value.createdAt,
    }
  } catch {
    return null
  }
}

export function clearPendingSocialLogin(): void {
  try {
    window.sessionStorage.removeItem(PENDING_KEY)
  } catch {
    // Không xóa được thì giá trị cũng tự hết hạn sau 10 phút.
  }
}

/**
 * Tạo state (và PKCE với Google), lấy địa chỉ trang đăng nhập từ backend, lưu phiên chờ rồi chuyển trang.
 * Lỗi (không gọi được backend) được ném ra để nơi gọi hiện thông báo.
 */
export async function beginSocialRedirect(
  provider: SocialProvider,
  mode: SocialLoginMode,
  redirect: unknown = null,
): Promise<void> {
  const state = randomUrlSafeString(32)
  const codeVerifier = provider === 'google' ? randomUrlSafeString(48) : null
  const url = await startSocialLogin(provider, {
    state,
    ...(codeVerifier ? { code_challenge: await pkceChallenge(codeVerifier) } : {}),
  })
  savePendingSocialLogin({
    provider,
    mode,
    state,
    codeVerifier,
    redirect: safeRedirect(redirect),
    createdAt: Date.now(),
  })
  navigateToExternal(url)
}
