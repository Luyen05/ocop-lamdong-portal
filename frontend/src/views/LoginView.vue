<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AuthLayout from '@/components/auth/AuthLayout.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { authStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()

const email = ref('')
const password = ref('')
const isSubmitting = ref(false)
const errorMessage = ref('')

async function submit(): Promise<void> {
  if (isSubmitting.value) return

  errorMessage.value = ''
  isSubmitting.value = true
  try {
    await authStore.login({ email: email.value, password: password.value })
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.push(redirect.startsWith('/') ? redirect : '/')
  } catch (error) {
    errorMessage.value = getApiErrorMessage(
      error,
      'Không thể đăng nhập. Vui lòng kiểm tra lại thông tin.',
    )
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <AuthLayout title="Đăng nhập" subtitle="Chào mừng bạn quay lại với OCOP Lâm Đồng.">
    <form class="d-grid gap-3" @submit.prevent="submit">
      <div v-if="errorMessage" class="alert alert-danger py-2" role="alert">
        {{ errorMessage }}
      </div>

      <div>
        <label class="form-label fw-semibold" for="login-email">Email</label>
        <input
          id="login-email"
          v-model.trim="email"
          class="form-control form-control-lg"
          type="email"
          autocomplete="email"
          placeholder="ban@example.com"
          required
        />
      </div>

      <div>
        <label class="form-label fw-semibold" for="login-password">Mật khẩu</label>
        <input
          id="login-password"
          v-model="password"
          class="form-control form-control-lg"
          type="password"
          autocomplete="current-password"
          placeholder="Nhập mật khẩu"
          required
        />
      </div>

      <button class="btn btn-success btn-lg mt-2" type="submit" :disabled="isSubmitting">
        <span
          v-if="isSubmitting"
          class="spinner-border spinner-border-sm me-2"
          aria-hidden="true"
        />
        {{ isSubmitting ? 'Đang đăng nhập...' : 'Đăng nhập' }}
      </button>

      <p class="mb-0 mt-2 text-center text-secondary">
        Chưa có tài khoản?
        <span class="fw-semibold text-success">Đăng ký sẽ được bổ sung ở bước kế tiếp</span>
      </p>
    </form>
  </AuthLayout>
</template>
