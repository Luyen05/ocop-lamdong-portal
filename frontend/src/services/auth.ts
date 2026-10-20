import http from '@/services/http'
import type {
  LoginPayload,
  RegisterPayload,
  SocialAuthorizePayload,
  SocialCallbackPayload,
  SocialLoginResponse,
  SocialProvider,
  SocialProvidersResponse,
  TokenResponse,
  UpdateProfilePayload,
  User,
} from '@/types/auth'

export async function register(payload: RegisterPayload): Promise<User> {
  const response = await http.post<User>('/auth/register', payload)
  return response.data
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const response = await http.post<TokenResponse>('/auth/login', payload)
  return response.data
}

export async function getMe(): Promise<User> {
  const response = await http.get<User>('/auth/me')
  return response.data
}

export async function updateMe(payload: UpdateProfilePayload): Promise<User> {
  const response = await http.patch<User>('/auth/me', payload)
  return response.data
}

export async function getSocialProviders(): Promise<SocialProvider[]> {
  const response = await http.get<SocialProvidersResponse>('/auth/social/providers')
  return response.data.providers
}

export async function startSocialLogin(
  provider: SocialProvider,
  payload: SocialAuthorizePayload,
): Promise<string> {
  const response = await http.post<{ authorization_url: string }>(
    `/auth/social/${provider}/authorize`,
    payload,
  )
  return response.data.authorization_url
}

export async function completeSocialLogin(
  provider: SocialProvider,
  payload: SocialCallbackPayload,
): Promise<SocialLoginResponse> {
  // Backend còn gọi Google/Facebook nên cho thời gian chờ dài hơn mặc định.
  const response = await http.post<SocialLoginResponse>(
    `/auth/social/${provider}/callback`,
    payload,
    { timeout: 30000 },
  )
  return response.data
}

/** Người dùng đang đăng nhập liên kết thêm Google/Facebook (sau khi Google/Facebook trả về). */
export async function linkSocialAccount(
  provider: SocialProvider,
  payload: SocialCallbackPayload,
): Promise<User> {
  const response = await http.post<User>(`/auth/social/${provider}/link`, payload, { timeout: 30000 })
  return response.data
}

export async function unlinkSocialAccount(provider: SocialProvider): Promise<User> {
  const response = await http.delete<User>(`/auth/social/${provider}`)
  return response.data
}
