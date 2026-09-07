export type UserRole = 'admin' | 'subject' | 'user'

export interface User {
  id: number
  email: string
  full_name: string
  phone: string | null
  avatar_url: string | null
  is_active: boolean
  role: UserRole
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
