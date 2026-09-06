<script setup lang="ts">
import { computed, ref } from 'vue'

import { getApiErrorMessage } from '@/services/api-error'
import { authStore } from '@/stores/auth'

const user = authStore.currentUser
const fullName = ref(user.value?.full_name ?? '')
const phone = ref(user.value?.phone ?? '')
const avatarUrl = ref(user.value?.avatar_url ?? '')
const isSubmitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const roleLabel = computed(() => {
  const labels = {
    admin: 'Quản trị viên',
    subject: 'Chủ thể OCOP',
    user: 'Người dùng',
  }
  return user.value ? labels[user.value.role] : ''
})

const joinedDate = computed(() => {
  if (!user.value) return ''
  return new Intl.DateTimeFormat('vi-VN', { dateStyle: 'long' }).format(
    new Date(user.value.created_at),
  )
})

async function submit(): Promise<void> {
  if (isSubmitting.value) return

  errorMessage.value = ''
  successMessage.value = ''
  isSubmitting.value = true
  try {
    await authStore.updateProfile({
      full_name: fullName.value,
      phone: phone.value || null,
      avatar_url: avatarUrl.value || null,
    })
    successMessage.value = 'Thông tin tài khoản đã được cập nhật.'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(
      error,
      'Không thể cập nhật hồ sơ. Vui lòng thử lại.',
    )
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="profile-page py-5">
    <div class="container">
      <div class="profile-heading mb-4">
        <div>
          <span class="text-success fw-semibold text-uppercase small">Tài khoản cá nhân</span>
          <h1 class="mt-2 mb-1">Thông tin của bạn</h1>
          <p class="mb-0 text-secondary">Quản lý thông tin dùng trên Cổng OCOP Lâm Đồng.</p>
        </div>
      </div>

      <div v-if="user" class="profile-grid">
        <aside class="profile-summary">
          <img
            v-if="user.avatar_url"
            class="profile-avatar"
            :src="user.avatar_url"
            :alt="`Ảnh đại diện của ${user.full_name}`"
          />
          <div v-else class="profile-avatar avatar-placeholder" aria-hidden="true">
            {{ user.full_name.charAt(0).toUpperCase() }}
          </div>
          <h2>{{ user.full_name }}</h2>
          <p>{{ user.email }}</p>
          <span class="role-badge">{{ roleLabel }}</span>
          <hr />
          <dl>
            <div>
              <dt>Ngày tham gia</dt>
              <dd>{{ joinedDate }}</dd>
            </div>
            <div>
              <dt>Trạng thái</dt>
              <dd class="text-success fw-semibold">Đang hoạt động</dd>
            </div>
          </dl>
        </aside>

        <section class="profile-form-card">
          <h2 class="h4 mb-1">Chỉnh sửa hồ sơ</h2>
          <p class="mb-4 text-secondary">
            Email, vai trò và trạng thái tài khoản chỉ do hệ thống quản lý.
          </p>

          <form class="d-grid gap-3" @submit.prevent="submit">
            <div v-if="errorMessage" class="alert alert-danger mb-0" role="alert">
              {{ errorMessage }}
            </div>
            <div v-if="successMessage" class="alert alert-success mb-0" role="status">
              {{ successMessage }}
            </div>

            <div>
              <label class="form-label fw-semibold" for="profile-email">Email</label>
              <input
                id="profile-email"
                class="form-control"
                type="email"
                :value="user.email"
                disabled
              />
            </div>

            <div>
              <label class="form-label fw-semibold" for="profile-name">Họ và tên</label>
              <input
                id="profile-name"
                v-model.trim="fullName"
                class="form-control"
                type="text"
                autocomplete="name"
                minlength="2"
                maxlength="150"
                required
              />
            </div>

            <div>
              <label class="form-label fw-semibold" for="profile-phone">Số điện thoại</label>
              <input
                id="profile-phone"
                v-model.trim="phone"
                class="form-control"
                type="tel"
                autocomplete="tel"
                minlength="8"
                maxlength="20"
                placeholder="Chưa cập nhật"
              />
            </div>

            <div>
              <label class="form-label fw-semibold" for="profile-avatar">URL ảnh đại diện</label>
              <input
                id="profile-avatar"
                v-model.trim="avatarUrl"
                class="form-control"
                type="url"
                maxlength="500"
                placeholder="https://..."
              />
              <div class="form-text">Upload ảnh lên Firebase sẽ được bổ sung trong module Ảnh.</div>
            </div>

            <div class="d-flex justify-content-end pt-2">
              <button class="btn btn-success px-4" type="submit" :disabled="isSubmitting">
                <span
                  v-if="isSubmitting"
                  class="spinner-border spinner-border-sm me-2"
                  aria-hidden="true"
                />
                {{ isSubmitting ? 'Đang lưu...' : 'Lưu thay đổi' }}
              </button>
            </div>
          </form>
        </section>
      </div>
    </div>
  </main>
</template>

<style scoped>
.profile-page {
  min-height: calc(100vh - 4.5rem);
  background: #f5f7f1;
}

.profile-heading h1 {
  color: #18351f;
  font-family: "Segoe UI", Arial, sans-serif;
  font-size: clamp(2rem, 4vw, 3rem);
}

.profile-grid {
  display: grid;
  gap: 1.5rem;
}

.profile-summary,
.profile-form-card {
  border: 1px solid rgb(29 72 39 / 10%);
  border-radius: 1.25rem;
  background: #fff;
  box-shadow: 0 0.8rem 2.5rem rgb(31 64 38 / 7%);
}

.profile-summary {
  padding: 2rem;
  text-align: center;
}

.profile-avatar {
  width: 6.5rem;
  height: 6.5rem;
  border: 0.35rem solid #edf4e5;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-placeholder {
  display: grid;
  margin-inline: auto;
  place-items: center;
  background: #2f6f3e;
  color: #fff;
  font-family: "Segoe UI", Arial, sans-serif;
  font-size: 2.75rem;
}

.profile-summary h2 {
  margin: 1rem 0 0.25rem;
  font-size: 1.3rem;
}

.profile-summary > p {
  margin-bottom: 0.75rem;
  color: #68736b;
}

.role-badge {
  display: inline-block;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  background: #e9f3df;
  color: #2f6f3e;
  font-size: 0.8rem;
  font-weight: 700;
}

.profile-summary hr {
  margin: 1.5rem 0;
  border-color: #dfe6dc;
}

.profile-summary dl {
  display: grid;
  gap: 1rem;
  margin: 0;
  text-align: left;
}

.profile-summary dl div {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.profile-summary dt,
.profile-summary dd {
  margin: 0;
  font-size: 0.88rem;
}

.profile-summary dt {
  color: #788078;
  font-weight: 500;
}

.profile-form-card {
  padding: clamp(1.5rem, 4vw, 2.5rem);
}

@media (min-width: 992px) {
  .profile-grid {
    grid-template-columns: minmax(15rem, 0.7fr) minmax(0, 1.5fr);
    align-items: start;
  }
}
</style>
