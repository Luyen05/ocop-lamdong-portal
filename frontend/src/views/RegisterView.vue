<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import AuthLayout from '@/components/auth/AuthLayout.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { authStore } from '@/stores/auth'

const router = useRouter()

const fullName = ref('')
const email = ref('')
const phone = ref('')
const password = ref('')
const passwordConfirmation = ref('')
const showPassword = ref(false)
const showPasswordConfirmation = ref(false)
const acceptedTerms = ref(false)
const isSubmitting = ref(false)
const errorMessage = ref('')

const passwordScore = computed(() => {
  let score = 0
  if (password.value.length >= 8) score += 1
  if (/[a-z]/.test(password.value) && /[A-Z]/.test(password.value)) score += 1
  if (/\d/.test(password.value)) score += 1
  if (/[^A-Za-z0-9]/.test(password.value)) score += 1
  return score
})

const passwordStrength = computed(() => {
  if (!password.value) return { label: 'Chưa nhập', tone: 'muted' }
  if (passwordScore.value <= 1) return { label: 'Yếu', tone: 'danger' }
  if (passwordScore.value <= 2) return { label: 'Trung bình', tone: 'warning' }
  return { label: 'Tốt', tone: 'success' }
})

const confirmationMismatch = computed(() =>
  Boolean(passwordConfirmation.value && password.value !== passwordConfirmation.value),
)

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
          <div class="input-group">
            <input
              id="register-password"
              v-model="password"
              class="form-control"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="new-password"
              minlength="8"
              maxlength="128"
              aria-describedby="password-strength"
              required
            />
            <button
              class="btn btn-outline-secondary password-toggle"
              type="button"
              :aria-label="showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'"
              :aria-pressed="showPassword"
              @click="showPassword = !showPassword"
            >
              <AppIcon :name="showPassword ? 'eyeSlash' : 'eye'" :size="17" />
            </button>
          </div>
          <div id="password-strength" class="password-strength" :data-tone="passwordStrength.tone">
            <span><i :style="{ width: `${passwordScore * 25}%` }" /></span>
            <small>Độ mạnh: {{ passwordStrength.label }}</small>
          </div>
        </div>
        <div class="col-md-6">
          <label class="form-label fw-semibold" for="register-confirmation">
            Xác nhận mật khẩu
          </label>
          <div class="input-group">
            <input
              id="register-confirmation"
              v-model="passwordConfirmation"
              class="form-control"
              :class="{ 'is-invalid': confirmationMismatch }"
              :type="showPasswordConfirmation ? 'text' : 'password'"
              autocomplete="new-password"
              minlength="8"
              maxlength="128"
              :aria-invalid="confirmationMismatch"
              aria-describedby="confirmation-feedback"
              required
            />
            <button
              class="btn btn-outline-secondary password-toggle"
              type="button"
              :aria-label="showPasswordConfirmation ? 'Ẩn mật khẩu xác nhận' : 'Hiện mật khẩu xác nhận'"
              :aria-pressed="showPasswordConfirmation"
              @click="showPasswordConfirmation = !showPasswordConfirmation"
            >
              <AppIcon :name="showPasswordConfirmation ? 'eyeSlash' : 'eye'" :size="17" />
            </button>
          </div>
          <div v-if="confirmationMismatch" id="confirmation-feedback" class="invalid-feedback d-block">
            Mật khẩu xác nhận chưa khớp.
          </div>
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

<style scoped>
.password-toggle {
  display: inline-grid;
  min-width: 44px;
  place-items: center;
}

.password-strength {
  display: grid;
  margin-top: 7px;
  grid-template-columns: minmax(72px, 1fr) auto;
  align-items: center;
  gap: var(--ocop-space-2);
  color: var(--ocop-text-secondary);
}

.password-strength > span {
  height: 5px;
  overflow: hidden;
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-surface-muted);
}

.password-strength i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--ocop-text-tertiary);
  transition: width var(--ocop-transition), background-color var(--ocop-transition);
}

.password-strength[data-tone='danger'] i { background: var(--ocop-danger); }
.password-strength[data-tone='warning'] i { background: var(--ocop-warning); }
.password-strength[data-tone='success'] i { background: var(--ocop-success); }

.password-strength small {
  min-width: 88px;
  font-size: var(--ocop-font-size-caption);
  text-align: right;
}
</style>
