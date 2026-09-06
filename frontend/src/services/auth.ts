import http from '@/services/http'
import type {
  LoginPayload,
  RegisterPayload,
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
