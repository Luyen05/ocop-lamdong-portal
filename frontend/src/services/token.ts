const ACCESS_TOKEN_KEY = 'ocop_access_token'

export function getAccessToken(): string | null {
  return window.localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function saveAccessToken(token: string): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

export function removeAccessToken(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY)
}
