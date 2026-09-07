<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, reactive, ref } from 'vue'

import { getApiErrorMessage } from '@/services/api-error'
import {
  createSubjectApplication,
  getMySubjectApplication,
  resubmitSubjectApplication,
} from '@/services/subjects'
import { authStore } from '@/stores/auth'
import type {
  SubjectApplication,
  SubjectApplicationPayload,
  SubjectStatus,
  SubjectType,
} from '@/types/subject'

const application = ref<SubjectApplication | null>(null)
const isLoading = ref(true)
const isSubmitting = ref(false)
const isEditing = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const form = reactive<SubjectApplicationPayload>({
  name: '',
  type: 'cooperative',
  tax_code: null,
  representative: authStore.currentUser.value?.full_name ?? '',
  phone: authStore.currentUser.value?.phone ?? '',
  email: authStore.currentUser.value?.email ?? null,
  address: '',
  district: '',
})

const statusLabels: Record<SubjectStatus, string> = {
  pending: 'Đang chờ duyệt',
  approved: 'Đã được duyệt',
  rejected: 'Cần bổ sung',
}

const typeLabels: Record<SubjectType, string> = {
  cooperative: 'Hợp tác xã',
  enterprise: 'Doanh nghiệp',
  household: 'Hộ kinh doanh',
  individual: 'Cá nhân / cơ sở sản xuất',
}

const pageDescription = computed(() => {
  if (!application.value) return 'Gửi thông tin đơn vị để quản trị viên xác minh.'
  if (application.value.status === 'approved') return 'Tài khoản của bạn đã được cấp quyền chủ thể.'
  if (application.value.status === 'rejected') return 'Cập nhật hồ sơ theo phản hồi và gửi lại để xét duyệt.'
  return 'Hồ sơ đang được quản trị viên kiểm tra.'
})

function fillForm(subject: SubjectApplication): void {
  form.name = subject.name
  form.type = subject.type
  form.tax_code = subject.tax_code
  form.representative = subject.representative
  form.phone = subject.phone
  form.email = subject.email
  form.address = subject.address
  form.district = subject.district
}

function startEditing(): void {
  if (!application.value) return
  fillForm(application.value)
  isEditing.value = true
  successMessage.value = ''
}

async function loadApplication(): Promise<void> {
  isLoading.value = true
  errorMessage.value = ''
  try {
    application.value = await getMySubjectApplication()
    fillForm(application.value)
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      application.value = null
    } else {
      errorMessage.value = getApiErrorMessage(error, 'Không thể tải hồ sơ chủ thể.')
    }
  } finally {
    isLoading.value = false
  }
}

async function submit(): Promise<void> {
  if (isSubmitting.value) return
  errorMessage.value = ''
  successMessage.value = ''
  isSubmitting.value = true
  const payload: SubjectApplicationPayload = {
    ...form,
    tax_code: form.tax_code || null,
    email: form.email || null,
  }
  try {
    application.value = application.value
      ? await resubmitSubjectApplication(payload)
      : await createSubjectApplication(payload)
    isEditing.value = false
    successMessage.value = 'Hồ sơ đã được gửi và đang chờ quản trị viên xét duyệt.'
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể gửi hồ sơ chủ thể.')
  } finally {
    isSubmitting.value = false
  }
}

onMounted(loadApplication)
</script>

<template>
  <main class="application-page">
    <div class="site-content application-content">
      <header class="page-heading">
        <div>
          <span>Chương trình OCOP Lâm Đồng</span>
          <h1>Hồ sơ đăng ký chủ thể</h1>
          <p>{{ pageDescription }}</p>
        </div>
        <RouterLink to="/tai-khoan">Quay lại tài khoản</RouterLink>
      </header>

      <div v-if="errorMessage" class="alert alert-danger" role="alert">
        {{ errorMessage }}
      </div>
      <div v-if="successMessage" class="alert alert-success" role="status">
        {{ successMessage }}
      </div>

      <section v-if="isLoading" class="state-card" aria-live="polite">
        <span class="spinner-border spinner-border-sm" aria-hidden="true" />
        Đang tải hồ sơ...
      </section>

      <template v-else>
        <section v-if="application && !isEditing" class="application-summary">
          <div class="summary-heading">
            <div>
              <span class="status-badge" :class="`status-${application.status}`">
                {{ statusLabels[application.status] }}
              </span>
              <h2>{{ application.name }}</h2>
              <p>{{ typeLabels[application.type] }} · {{ application.district }}</p>
            </div>
            <button
              v-if="application.status !== 'approved'"
              class="btn btn-outline-success"
              type="button"
              @click="startEditing"
            >
              Chỉnh sửa hồ sơ
            </button>
          </div>

          <div v-if="application.moderation_note" class="moderation-note">
            <strong>Phản hồi từ quản trị viên</strong>
            <p>{{ application.moderation_note }}</p>
          </div>

          <dl class="application-details">
            <div><dt>Người đại diện</dt><dd>{{ application.representative }}</dd></div>
            <div><dt>Mã số thuế</dt><dd>{{ application.tax_code || 'Chưa cung cấp' }}</dd></div>
            <div><dt>Số điện thoại</dt><dd>{{ application.phone }}</dd></div>
            <div><dt>Email đơn vị</dt><dd>{{ application.email || 'Chưa cung cấp' }}</dd></div>
            <div class="full-row"><dt>Địa chỉ</dt><dd>{{ application.address }}</dd></div>
          </dl>
        </section>

        <section v-else class="application-form-card">
          <div class="form-intro">
            <span>{{ application ? 'Cập nhật hồ sơ' : 'Thông tin đăng ký' }}</span>
            <h2>{{ application ? 'Bổ sung thông tin chủ thể' : 'Đăng ký trở thành chủ thể OCOP' }}</h2>
            <p>Thông tin sẽ được quản trị viên kiểm tra trước khi cấp quyền quản lý sản phẩm.</p>
          </div>

          <form class="application-form" @submit.prevent="submit">
            <label>
              <span>Tên đơn vị / cơ sở *</span>
              <input v-model.trim="form.name" class="form-control" minlength="2" maxlength="255" required />
            </label>
            <label>
              <span>Loại hình *</span>
              <select v-model="form.type" class="form-select" required>
                <option v-for="(label, value) in typeLabels" :key="value" :value="value">{{ label }}</option>
              </select>
            </label>
            <label>
              <span>Người đại diện *</span>
              <input v-model.trim="form.representative" class="form-control" minlength="2" maxlength="150" required />
            </label>
            <label>
              <span>Mã số thuế</span>
              <input v-model.trim="form.tax_code" class="form-control" maxlength="50" />
            </label>
            <label>
              <span>Số điện thoại *</span>
              <input v-model.trim="form.phone" class="form-control" type="tel" minlength="8" maxlength="20" required />
            </label>
            <label>
              <span>Email đơn vị</span>
              <input v-model.trim="form.email" class="form-control" type="email" />
            </label>
            <label>
              <span>Huyện / thành phố *</span>
              <input v-model.trim="form.district" class="form-control" minlength="2" maxlength="100" placeholder="Ví dụ: Đà Lạt" required />
            </label>
            <label class="full-row">
              <span>Địa chỉ hoạt động *</span>
              <textarea v-model.trim="form.address" class="form-control" rows="3" minlength="5" maxlength="1000" required />
            </label>

            <div class="form-actions full-row">
              <button
                v-if="application"
                class="btn btn-light"
                type="button"
                @click="isEditing = false"
              >
                Hủy
              </button>
              <button class="btn btn-success px-4" type="submit" :disabled="isSubmitting">
                {{ isSubmitting ? 'Đang gửi...' : application ? 'Gửi lại hồ sơ' : 'Gửi hồ sơ' }}
              </button>
            </div>
          </form>
        </section>
      </template>
    </div>
  </main>
</template>

<style scoped>
.application-page {
  min-height: 70vh;
  padding: 48px 0 64px;
  background: var(--ocop-surface);
}

.application-content {
  display: grid;
  gap: 20px;
}

.page-heading,
.summary-heading,
.form-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.page-heading span,
.form-intro > span {
  color: var(--ocop-primary-700);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.page-heading h1 {
  margin: 6px 0;
  font-size: clamp(28px, 4vw, 42px);
  font-weight: 800;
}

.page-heading p,
.form-intro p,
.summary-heading p {
  margin: 0;
  color: var(--ocop-slate);
}

.page-heading a {
  color: var(--ocop-primary-700);
  font-weight: 700;
  text-decoration: none;
}

.state-card,
.application-summary,
.application-form-card {
  padding: clamp(22px, 4vw, 36px);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: #fff;
  box-shadow: 0 16px 35px rgb(15 23 43 / 6%);
}

.state-card {
  display: flex;
  align-items: center;
  gap: 10px;
}

.summary-heading h2,
.form-intro h2 {
  margin: 10px 0 4px;
  font-size: 24px;
  font-weight: 800;
}

.status-badge {
  display: inline-flex;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
}

.status-pending { background: #fff7d6; color: #8a5900; }
.status-approved { background: var(--ocop-mint-soft); color: var(--ocop-primary-900); }
.status-rejected { background: #fff0f1; color: #b4232c; }

.moderation-note {
  margin-top: 22px;
  padding: 16px;
  border-left: 4px solid var(--ocop-gold);
  border-radius: 8px;
  background: #fffbeb;
}

.moderation-note p { margin: 4px 0 0; }

.application-details,
.application-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px 24px;
}

.application-details {
  margin: 26px 0 0;
}

.application-details div,
.application-form label {
  display: grid;
  gap: 7px;
}

.application-details dt,
.application-form label > span {
  color: var(--ocop-slate);
  font-size: 12px;
  font-weight: 700;
}

.application-details dd { margin: 0; font-weight: 650; }
.full-row { grid-column: 1 / -1; }
.application-form { margin-top: 26px; }
.form-actions { justify-content: flex-end; padding-top: 6px; }

@media (max-width: 767.98px) {
  .application-page { padding-top: 28px; }
  .page-heading,
  .summary-heading { align-items: flex-start; flex-direction: column; }
  .application-details,
  .application-form { grid-template-columns: 1fr; }
  .full-row { grid-column: auto; }
}
</style>
