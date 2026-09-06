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

export function expireAccessToken(): void {
  removeAccessToken()
  window.dispatchEvent(new Event(AUTH_SESSION_EXPIRED_EVENT))
}
