export type UserRole = 'admin' | 'subject' | 'user'
export type SocialProvider = 'google' | 'facebook'

export interface User {
  id: number
  email: string
  full_name: string
  phone: string | null
  avatar_url: string | null
  is_active: boolean
  role: UserRole
  /** false: tài khoản tạo bằng Google/Facebook, chưa có mật khẩu. */
  has_password?: boolean
  social_providers?: readonly SocialProvider[]
  created_at: string
  updated_at: string
}

export interface RegisterPayload {
  email: string
  password: string
  full_name: string
  phone?: string | null
}

export interface LoginPayload {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: 'bearer'
  expires_in: number
}

export interface UpdateProfilePayload {
  full_name?: string
  phone?: string | null
  avatar_url?: string | null
}

/** Đổi mật khẩu; tài khoản chưa có mật khẩu (Google/Facebook) không gửi current_password. */
export interface ChangePasswordPayload {
  current_password?: string
  new_password: string
}

export interface SocialProvidersResponse {
  providers: SocialProvider[]
}

export interface SocialAuthorizePayload {
  state: string
  code_challenge?: string
}

export interface SocialCallbackPayload {
  code: string
  code_verifier?: string
}

export interface SocialLoginResponse extends TokenResponse {
  is_new_user: boolean
}
