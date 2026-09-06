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
  } catch {
    clearSession()
  } finally {
    initialized = true
    isInitializing.value = false
  }
}

async function login(payload: LoginPayload): Promise<User> {
  const token = await authService.login(payload)
  saveAccessToken(token.access_token)
  accessToken.value = token.access_token

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
  register,
  updateProfile,
  logout: clearSession,
}
