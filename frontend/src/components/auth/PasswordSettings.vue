<script setup lang="ts">
import { computed, ref } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { changePassword } from '@/services/auth'
import { authStore } from '@/stores/auth'
import {
  PASSWORD_MAX_LENGTH,
  PASSWORD_MIN_LENGTH,
  getPasswordScore,
  getPasswordStrength,
} from '@/utils/password'

const user = authStore.currentUser
/** Tài khoản tạo bằng Google/Facebook chưa có mật khẩu: đặt mật khẩu, không hỏi mật khẩu hiện tại. */
const isSettingFirstPassword = computed(() => user.value?.has_password === false)

const currentPassword = ref('')
const newPassword = ref('')
const confirmation = ref('')
const showCurrent = ref(false)
const showNew = ref(false)
const showConfirmation = ref(false)
const isSubmitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const score = computed(() => getPasswordScore(newPassword.value))
const strength = computed(() => getPasswordStrength(newPassword.value))
const confirmationMismatch = computed(() =>
  Boolean(confirmation.value && newPassword.value !== confirmation.value),
)

function reset(): void {
  currentPassword.value = ''
  newPassword.value = ''
  confirmation.value = ''
  showCurrent.value = false
  showNew.value = false
  showConfirmation.value = false
}

async function submit(): Promise<void> {
  if (isSubmitting.value) return

  errorMessage.value = ''
  successMessage.value = ''
  if (newPassword.value.length < PASSWORD_MIN_LENGTH) {
    errorMessage.value = `Mật khẩu mới cần ít nhất ${PASSWORD_MIN_LENGTH} ký tự.`
    return
  }
  if (newPassword.value !== confirmation.value) {
    errorMessage.value = 'Mật khẩu nhập lại chưa khớp.'
    return
  }

  const settingFirst = isSettingFirstPassword.value
  isSubmitting.value = true
  try {
    await changePassword(
      settingFirst
        ? { new_password: newPassword.value }
        : { current_password: currentPassword.value, new_password: newPassword.value },
    )
    reset()
    successMessage.value = settingFirst
      ? 'Đã đặt mật khẩu. Lần sau bạn có thể đăng nhập bằng email và mật khẩu.'
      : 'Đã đổi mật khẩu.'
    try {
      await authStore.refreshUser()
    } catch {
      // Mật khẩu đã đổi thành công; thông tin tài khoản sẽ cập nhật ở lần tải trang sau.
    }
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể lưu mật khẩu. Vui lòng thử lại.')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <section v-if="user" class="password-settings" aria-labelledby="password-settings-title" data-testid="password-settings">
    <h2 id="password-settings-title" class="h4 mb-1">
      {{ isSettingFirstPassword ? 'Đặt mật khẩu' : 'Mật khẩu' }}
    </h2>
    <p class="mb-4 text-secondary">
      <template v-if="isSettingFirstPassword">
        Tài khoản của bạn đang đăng nhập bằng Google/Facebook. Đặt mật khẩu để có thể đăng nhập bằng email
        {{ user.email }}.
      </template>
      <template v-else>Đổi mật khẩu đăng nhập bằng email. Mật khẩu mới cần ít nhất 8 ký tự.</template>
    </p>

    <form class="d-grid gap-3" novalidate @submit.prevent="submit">
      <div v-if="errorMessage" class="alert alert-danger mb-0" role="alert">{{ errorMessage }}</div>
      <div v-if="successMessage" class="alert alert-success mb-0" role="status">{{ successMessage }}</div>

      <div v-if="!isSettingFirstPassword">
        <label class="form-label fw-semibold" for="current-password">Mật khẩu hiện tại</label>
        <div class="input-group">
          <input
            id="current-password"
            v-model="currentPassword"
            class="form-control"
            :type="showCurrent ? 'text' : 'password'"
            autocomplete="current-password"
            :maxlength="PASSWORD_MAX_LENGTH"
            required
          />
          <button
            class="btn btn-outline-secondary password-toggle"
            type="button"
            :aria-label="showCurrent ? 'Ẩn mật khẩu hiện tại' : 'Hiện mật khẩu hiện tại'"
            :aria-pressed="showCurrent"
            @click="showCurrent = !showCurrent"
          >
            <AppIcon :name="showCurrent ? 'eyeSlash' : 'eye'" :size="17" />
          </button>
        </div>
      </div>

      <div class="row g-3">
        <div class="col-md-6">
          <label class="form-label fw-semibold" for="new-password">Mật khẩu mới</label>
          <div class="input-group">
            <input
              id="new-password"
              v-model="newPassword"
              class="form-control"
              :type="showNew ? 'text' : 'password'"
              autocomplete="new-password"
              :minlength="PASSWORD_MIN_LENGTH"
              :maxlength="PASSWORD_MAX_LENGTH"
              aria-describedby="new-password-strength"
              required
            />
            <button
              class="btn btn-outline-secondary password-toggle"
              type="button"
              :aria-label="showNew ? 'Ẩn mật khẩu mới' : 'Hiện mật khẩu mới'"
              :aria-pressed="showNew"
              @click="showNew = !showNew"
            >
              <AppIcon :name="showNew ? 'eyeSlash' : 'eye'" :size="17" />
            </button>
          </div>
          <div id="new-password-strength" class="password-strength" :data-tone="strength.tone">
            <span><i :style="{ width: `${score * 25}%` }" /></span>
            <small>Độ mạnh: {{ strength.label }}</small>
          </div>
        </div>
        <div class="col-md-6">
          <label class="form-label fw-semibold" for="new-password-confirmation">Nhập lại mật khẩu mới</label>
          <div class="input-group">
            <input
              id="new-password-confirmation"
              v-model="confirmation"
              class="form-control"
              :class="{ 'is-invalid': confirmationMismatch }"
              :type="showConfirmation ? 'text' : 'password'"
              autocomplete="new-password"
              :minlength="PASSWORD_MIN_LENGTH"
              :maxlength="PASSWORD_MAX_LENGTH"
              :aria-invalid="confirmationMismatch"
              aria-describedby="new-password-confirmation-feedback"
              required
            />
            <button
              class="btn btn-outline-secondary password-toggle"
              type="button"
              :aria-label="showConfirmation ? 'Ẩn mật khẩu nhập lại' : 'Hiện mật khẩu nhập lại'"
              :aria-pressed="showConfirmation"
              @click="showConfirmation = !showConfirmation"
            >
              <AppIcon :name="showConfirmation ? 'eyeSlash' : 'eye'" :size="17" />
            </button>
          </div>
          <div
            v-if="confirmationMismatch"
            id="new-password-confirmation-feedback"
            class="invalid-feedback d-block"
          >
            Mật khẩu nhập lại chưa khớp.
          </div>
        </div>
      </div>

      <div class="d-flex justify-content-end pt-2">
        <button class="btn btn-success px-4 submit-button" type="submit" :disabled="isSubmitting">
          <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2" aria-hidden="true" />
          <template v-if="isSubmitting">Đang lưu...</template>
          <template v-else>{{ isSettingFirstPassword ? 'Đặt mật khẩu' : 'Đổi mật khẩu' }}</template>
        </button>
      </div>
    </form>
  </section>
</template>

<style scoped>
.password-toggle {
  display: inline-grid;
  min-width: 44px;
  place-items: center;
}

.submit-button {
  min-height: 44px;
}

.password-strength {
  display: grid;
  margin-top: var(--ocop-space-2);
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

@media (prefers-reduced-motion: reduce) {
  .password-strength i { transition: none; }
}
</style>
