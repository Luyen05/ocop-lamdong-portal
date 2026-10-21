const ACCESS_TOKEN_KEY = 'ocop_access_token'
export const AUTH_SESSION_EXPIRED_EVENT = 'ocop:auth-session-expired'

export function getAccessToken(): string | null {
  return window.localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function saveAccessToken(token: string): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

export function removeAccessToken(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY)
}

/** Lý do kết thúc phiên: hết hạn token, hoặc tài khoản bị quản trị viên khóa. */
export type SessionEndReason = 'expired' | 'locked'

export function expireAccessToken(reason: SessionEndReason = 'expired'): void {
  removeAccessToken()
  window.dispatchEvent(new CustomEvent<SessionEndReason>(AUTH_SESSION_EXPIRED_EVENT, { detail: reason }))
}
