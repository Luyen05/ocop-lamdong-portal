import axios from 'axios'
import { computed, readonly, ref } from 'vue'

import * as authService from '@/services/auth'
import {
  AUTH_SESSION_EXPIRED_EVENT,
  getAccessToken,
  removeAccessToken,
  saveAccessToken,
} from '@/services/token'
import type {
  LoginPayload,
  RegisterPayload,
  UpdateProfilePayload,
  User,
} from '@/types/auth'

const currentUser = ref<User | null>(null)
const accessToken = ref<string | null>(getAccessToken())
const isInitializing = ref(false)
let initialized = false

const isAuthenticated = computed(() => Boolean(accessToken.value && currentUser.value))

async function initialize(): Promise<void> {
  if (initialized || !accessToken.value) {
    initialized = true
    return
  }

  isInitializing.value = true
  try {
    currentUser.value = await authService.getMe()
    initialized = true
  } catch (error) {
    if (isRejectedToken(error)) {
      // Token hết hạn hoặc không hợp lệ: xóa phiên.
      clearSession()
      initialized = true
    }
    // Lỗi mạng hoặc máy chủ tạm lỗi: giữ token, lần chuyển trang sau thử lại thay vì đăng xuất người dùng.
  } finally {
    isInitializing.value = false
  }
}

function isRejectedToken(error: unknown): boolean {
  const status = axios.isAxiosError(error) ? error.response?.status : undefined
  return status === 401 || status === 403
}

async function login(payload: LoginPayload): Promise<User> {
  const token = await authService.login(payload)
  return loginWithToken(token.access_token)
}

/** Lưu token (đăng nhập mật khẩu hoặc Google/Facebook) rồi tải thông tin người dùng. */
async function loginWithToken(token: string): Promise<User> {
  saveAccessToken(token)
  accessToken.value = token

  try {
    currentUser.value = await authService.getMe()
    return currentUser.value
  } catch (error) {
    clearSession()
    throw error
  }
}

async function register(payload: RegisterPayload): Promise<User> {
  return authService.register(payload)
}

async function updateProfile(payload: UpdateProfilePayload): Promise<User> {
  const user = await authService.updateMe(payload)
  currentUser.value = user
  return user
}

/**
 * Tải lại người dùng hiện tại từ /auth/me, ví dụ sau khi đặt mật khẩu (has_password đổi) hoặc
 * khi hồ sơ chủ thể vừa được duyệt (vai trò đổi từ user sang subject).
 */
async function refreshUser(): Promise<User | null> {
  if (!accessToken.value) return null
  currentUser.value = await authService.getMe()
  return currentUser.value
}

/** Cập nhật người dùng hiện tại từ kết quả API (ví dụ sau khi liên kết Google/Facebook). */
function setCurrentUser(user: User): void {
  currentUser.value = user
}

function clearSession(): void {
  removeAccessToken()
  accessToken.value = null
  currentUser.value = null
}

window.addEventListener(AUTH_SESSION_EXPIRED_EVENT, () => {
  accessToken.value = null
  currentUser.value = null
})

export const authStore = {
  currentUser: readonly(currentUser),
  isAuthenticated,
  isInitializing: readonly(isInitializing),
  initialize,
  login,
  loginWithToken,
  register,
  updateProfile,
  refreshUser,
  setCurrentUser,
  logout: clearSession,
}
