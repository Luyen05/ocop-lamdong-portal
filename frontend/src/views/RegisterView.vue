<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import AuthLayout from '@/components/auth/AuthLayout.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { authStore } from '@/stores/auth'

const router = useRouter()

const fullName = ref('')
const email = ref('')
const phone = ref('')
const password = ref('')
const passwordConfirmation = ref('')
const acceptedTerms = ref(false)
const isSubmitting = ref(false)
const errorMessage = ref('')

async function submit(): Promise<void> {
  if (isSubmitting.value) return

  errorMessage.value = ''
  if (password.value !== passwordConfirmation.value) {
    errorMessage.value = 'Mật khẩu xác nhận chưa khớp.'
    return
  }

  isSubmitting.value = true
  try {
    await authStore.register({
      email: email.value,
      password: password.value,
      full_name: fullName.value,
      phone: phone.value || null,
    })
    await router.push({
      name: 'login',
      query: { registered: '1', email: email.value },
    })
  } catch (error) {
    errorMessage.value = getApiErrorMessage(
      error,
      'Không thể tạo tài khoản. Vui lòng thử lại.',
    )
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <AuthLayout
    title="Tạo tài khoản"
    subtitle="Đăng ký để đánh giá và lưu lại trải nghiệm của bạn."
  >
    <form class="d-grid gap-3" @submit.prevent="submit">
      <div v-if="errorMessage" class="alert alert-danger py-2" role="alert">
        {{ errorMessage }}
      </div>

      <div>
        <label class="form-label fw-semibold" for="register-name">Họ và tên</label>
        <input
          id="register-name"
          v-model.trim="fullName"
          class="form-control"
          type="text"
          autocomplete="name"
          minlength="2"
          maxlength="150"
          required
        />
      </div>

      <div class="row g-3">
        <div class="col-md-7">
          <label class="form-label fw-semibold" for="register-email">Email</label>
          <input
            id="register-email"
            v-model.trim="email"
            class="form-control"
            type="email"
            autocomplete="email"
            required
          />
        </div>
        <div class="col-md-5">
          <label class="form-label fw-semibold" for="register-phone">Điện thoại</label>
          <input
            id="register-phone"
            v-model.trim="phone"
            class="form-control"
            type="tel"
            autocomplete="tel"
            minlength="8"
            maxlength="20"
            placeholder="Không bắt buộc"
          />
        </div>
      </div>

      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label fw-semibold" for="register-password">Mật khẩu</label>
          <input
            id="register-password"
            v-model="password"
            class="form-control"
            type="password"
            autocomplete="new-password"
            minlength="8"
            maxlength="128"
            required
          />
        </div>
        <div class="col-md-6">
          <label class="form-label fw-semibold" for="register-confirmation">
            Xác nhận mật khẩu
          </label>
          <input
            id="register-confirmation"
            v-model="passwordConfirmation"
            class="form-control"
            type="password"
            autocomplete="new-password"
            minlength="8"
            maxlength="128"
            required
          />
        </div>
      </div>

      <div class="form-check">
        <input
          id="accepted-terms"
          v-model="acceptedTerms"
          class="form-check-input"
          type="checkbox"
          required
        />
        <label class="form-check-label text-secondary" for="accepted-terms">
          Tôi đồng ý cung cấp thông tin để tạo tài khoản trên hệ thống.
        </label>
      </div>

      <button class="btn btn-success btn-lg" type="submit" :disabled="isSubmitting">
        <span
          v-if="isSubmitting"
          class="spinner-border spinner-border-sm me-2"
          aria-hidden="true"
        />
        {{ isSubmitting ? 'Đang tạo tài khoản...' : 'Đăng ký' }}
      </button>

      <p class="mb-0 text-center text-secondary">
        Đã có tài khoản?
        <RouterLink class="fw-semibold text-success" to="/dang-nhap">Đăng nhập</RouterLink>
      </p>
    </form>
  </AuthLayout>
</template>
