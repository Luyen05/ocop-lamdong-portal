<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import StatusPanel from '@/components/ui/StatusPanel.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { getSubjectProfile, updateSubjectProfile } from '@/services/subjects'
import type { SubjectApplication, SubjectProfileUpdatePayload } from '@/types/subject'

const subject = ref<SubjectApplication | null>(null)
const loading = ref(true)
const loadError = ref('')
const isEditing = ref(false)
const isSaving = ref(false)
const saveError = ref('')
const successMessage = ref('')

const form = reactive({
  representative: '',
  phone: '',
  email: '',
  address: '',
  district: '',
})

const statusLabel = computed(() => {
  if (subject.value?.status === 'approved') return 'Đã được duyệt'
  if (subject.value?.status === 'rejected') return 'Cần bổ sung'
  return 'Đang chờ duyệt'
})

const typeLabels = {
  cooperative: 'Hợp tác xã',
  enterprise: 'Doanh nghiệp',
  household: 'Hộ kinh doanh',
  individual: 'Cá nhân',
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('vi-VN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function fillForm(profile: SubjectApplication): void {
  form.representative = profile.representative
  form.phone = profile.phone
  form.email = profile.email ?? ''
  form.address = profile.address
  form.district = profile.district
}

async function loadProfile(): Promise<void> {
  loading.value = true
  loadError.value = ''
  try {
    subject.value = await getSubjectProfile()
    fillForm(subject.value)
  } catch (error) {
    loadError.value = getApiErrorMessage(error, 'Không thể tải hồ sơ chủ thể.')
  } finally {
    loading.value = false
  }
}

function startEditing(): void {
  if (!subject.value) return
  fillForm(subject.value)
  saveError.value = ''
  successMessage.value = ''
  isEditing.value = true
}

function cancelEditing(): void {
  if (isSaving.value) return
  if (subject.value) fillForm(subject.value)
  saveError.value = ''
  isEditing.value = false
}

/** Chỉ gửi các trường đã đổi. */
function changedFields(): SubjectProfileUpdatePayload {
  const current = subject.value
  if (!current) return {}
  const payload: SubjectProfileUpdatePayload = {}
  const representative = form.representative.trim()
  const phone = form.phone.trim()
  const email = form.email.trim() || null
  const address = form.address.trim()
  const district = form.district.trim()
  if (representative !== current.representative) payload.representative = representative
  if (phone !== current.phone) payload.phone = phone
  if (email !== (current.email ?? null)) payload.email = email
  if (address !== current.address) payload.address = address
  if (district !== current.district) payload.district = district
  return payload
}

async function save(): Promise<void> {
  if (isSaving.value) return
  saveError.value = ''
  successMessage.value = ''
  const payload = changedFields()
  if (Object.keys(payload).length === 0) {
    isEditing.value = false
    successMessage.value = 'Không có thay đổi nào cần lưu.'
    return
  }
  isSaving.value = true
  try {
    subject.value = await updateSubjectProfile(payload)
    fillForm(subject.value)
    isEditing.value = false
    successMessage.value = 'Đã lưu thông tin liên hệ của đơn vị.'
  } catch (error) {
    saveError.value = getApiErrorMessage(error, 'Không thể lưu thông tin. Vui lòng thử lại.')
  } finally {
    isSaving.value = false
  }
}

onMounted(loadProfile)
</script>

<template>
  <main class="profile-page stagger-in">
    <header class="page-heading">
      <div>
        <span>THÔNG TIN ĐƠN VỊ</span>
        <h1>Hồ sơ chủ thể</h1>
        <p>Thông tin đã được quản trị viên xác minh để cấp quyền quản lý sản phẩm.</p>
      </div>
      <RouterLink class="account-link" to="/tai-khoan">Sửa thông tin tài khoản</RouterLink>
    </header>

    <StatusPanel v-if="loading" kind="loading" :rows="2" message="Đang tải hồ sơ…" />
    <StatusPanel
      v-else-if="loadError"
      kind="error"
      title="Chưa tải được hồ sơ chủ thể"
      :message="loadError"
      @retry="loadProfile"
    />

    <template v-else-if="subject">
      <section class="summary-card">
        <div class="subject-mark" aria-hidden="true">{{ subject.name.charAt(0).toUpperCase() }}</div>
        <div class="subject-name">
          <span class="status-badge" :class="`status-${subject.status}`">{{ statusLabel }}</span>
          <h2>{{ subject.name }}</h2>
          <p>{{ typeLabels[subject.type] }} · {{ subject.district }}</p>
        </div>
        <div class="review-time">
          <small>Cập nhật gần nhất</small>
          <strong>{{ formatDate(subject.updated_at) }}</strong>
        </div>
      </section>

      <section v-if="subject.moderation_note" class="review-note">
        <strong>Phản hồi gần nhất từ quản trị viên</strong>
        <p>{{ subject.moderation_note }}</p>
      </section>

      <section class="details-card" aria-labelledby="identity-title" data-testid="identity-card">
        <div class="card-heading">
          <div><span>HỒ SƠ PHÁP LÝ</span><h2 id="identity-title">Thông tin định danh</h2></div>
          <small>Chỉ xem</small>
        </div>
        <dl>
          <div class="wide"><dt>Tên đơn vị</dt><dd>{{ subject.name }}</dd></div>
          <div><dt>Loại hình</dt><dd>{{ typeLabels[subject.type] }}</dd></div>
          <div><dt>Mã số thuế</dt><dd>{{ subject.tax_code || 'Chưa cung cấp' }}</dd></div>
        </dl>
        <p class="locked-note">
          Tên đơn vị, loại hình và mã số thuế đã được xác minh nên không tự sửa được.
          Khi các thông tin này thay đổi, vui lòng liên hệ quản trị viên.
        </p>
      </section>

      <section class="details-card" aria-labelledby="contact-title" data-testid="contact-card">
        <div class="card-heading">
          <div><span>LIÊN HỆ</span><h2 id="contact-title">Thông tin liên hệ</h2></div>
          <button
            v-if="!isEditing"
            class="ocop-btn-ghost edit-button"
            type="button"
            data-testid="edit-contact"
            @click="startEditing"
          >
            Sửa thông tin liên hệ
          </button>
        </div>

        <div v-if="successMessage" class="alert alert-success mt-3 mb-0" role="status">{{ successMessage }}</div>

        <dl v-if="!isEditing">
          <div><dt>Người đại diện</dt><dd>{{ subject.representative }}</dd></div>
          <div><dt>Số điện thoại</dt><dd>{{ subject.phone }}</dd></div>
          <div><dt>Email đơn vị</dt><dd>{{ subject.email || 'Chưa cung cấp' }}</dd></div>
          <div><dt>Khu vực</dt><dd>{{ subject.district }}</dd></div>
          <div class="wide"><dt>Địa chỉ</dt><dd>{{ subject.address }}</dd></div>
        </dl>

        <form v-else class="contact-form" data-testid="contact-form" @submit.prevent="save">
          <div v-if="saveError" class="alert alert-danger mb-0 wide" role="alert">{{ saveError }}</div>
          <div>
            <label class="form-label fw-semibold" for="subject-representative">Người đại diện</label>
            <input
              id="subject-representative"
              v-model="form.representative"
              class="form-control"
              autocomplete="name"
              minlength="2"
              maxlength="150"
              required
            />
          </div>
          <div>
            <label class="form-label fw-semibold" for="subject-phone">Số điện thoại</label>
            <input
              id="subject-phone"
              v-model="form.phone"
              class="form-control"
              type="tel"
              autocomplete="tel"
              minlength="8"
              maxlength="20"
              required
            />
          </div>
          <div>
            <label class="form-label fw-semibold" for="subject-email">Email đơn vị</label>
            <input
              id="subject-email"
              v-model="form.email"
              class="form-control"
              type="email"
              autocomplete="email"
              maxlength="150"
              placeholder="Không bắt buộc"
            />
          </div>
          <div>
            <label class="form-label fw-semibold" for="subject-district">Khu vực (xã, phường)</label>
            <input
              id="subject-district"
              v-model="form.district"
              class="form-control"
              minlength="2"
              maxlength="100"
              placeholder="Ví dụ: Đà Lạt"
              required
            />
          </div>
          <div class="wide">
            <label class="form-label fw-semibold" for="subject-address">Địa chỉ</label>
            <textarea
              id="subject-address"
              v-model="form.address"
              class="form-control"
              rows="3"
              minlength="5"
              maxlength="1000"
              required
            />
          </div>
          <div class="form-actions wide">
            <button class="ocop-btn-ghost" type="button" :disabled="isSaving" @click="cancelEditing">Hủy</button>
            <button class="btn btn-success px-4" type="submit" :disabled="isSaving">
              <span v-if="isSaving" class="spinner-border spinner-border-sm me-2" aria-hidden="true" />
              {{ isSaving ? 'Đang lưu...' : 'Lưu thay đổi' }}
            </button>
          </div>
        </form>
      </section>

      <aside class="profile-help">
        <div>
          <strong>Cần đổi tên đơn vị hoặc mã số thuế?</strong>
          <p>Những thông tin này gắn với giấy tờ đã xác minh. Hãy liên hệ quản trị viên để được cập nhật.</p>
        </div>
        <RouterLink to="/">Về trang công khai</RouterLink>
      </aside>
    </template>
  </main>
</template>

<style scoped>
.profile-page { display: grid; max-width: 980px; margin-inline: auto; gap: 18px; }
.page-heading { display: flex; align-items: end; justify-content: space-between; gap: var(--ocop-space-5); }
.page-heading span, .card-heading span { color: var(--ocop-primary-700); font-size: var(--ocop-font-size-caption); font-weight: 800; letter-spacing: .05em; }
.page-heading h1 { margin: var(--ocop-space-1) 0; color: var(--ocop-navy); font-size: 30px; }
.page-heading p { margin: 0; color: var(--ocop-slate); font-size: var(--ocop-font-size-small); }
.account-link, .profile-help a { display: inline-flex; min-height: 44px; padding: 10px 14px; align-items: center; justify-content: center; border: 1px solid var(--ocop-primary-700); border-radius: 9px; color: var(--ocop-primary-700); font-size: var(--ocop-font-size-caption); font-weight: 750; text-decoration: none; white-space: nowrap; }
.summary-card, .details-card, .review-note, .profile-help { border: 1px solid var(--ocop-border); border-radius: 14px; background: var(--ocop-card); }
.summary-card { display: grid; padding: 22px; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: var(--ocop-space-4); }
.subject-mark { display: grid; width: 54px; height: 54px; place-items: center; border-radius: 14px; background: var(--ocop-success-soft); color: var(--ocop-primary-700); font-size: 22px; font-weight: 800; }
.status-badge { display: inline-flex; width: fit-content; padding: 3px var(--ocop-space-2); border-radius: var(--ocop-radius-pill); background: var(--ocop-warning-surface); color: var(--ocop-warning-strong); font-size: var(--ocop-font-size-caption); font-weight: 800; text-transform: uppercase; }
.status-approved { background: var(--ocop-success-soft); color: var(--ocop-success); }
.status-rejected { background: var(--ocop-danger-soft); color: var(--ocop-danger); }
.subject-name h2 { margin: 5px 0 2px; color: var(--ocop-navy); font-size: 20px; }
.subject-name p, .review-note p, .profile-help p { margin: 0; color: var(--ocop-slate); font-size: var(--ocop-font-size-caption); }
.review-time { display: grid; text-align: right; }
.review-time small { color: var(--ocop-slate); font-size: var(--ocop-font-size-caption); }
.review-time strong { font-size: var(--ocop-font-size-caption); }
.review-note { padding: 17px var(--ocop-space-5); border-color: var(--ocop-warning-border); background: var(--ocop-warning-soft); }
.review-note strong { color: var(--ocop-warning); font-size: var(--ocop-font-size-caption); }
.review-note p { margin: 5px 0 0; color: var(--ocop-warning); }
.details-card { padding: 22px; }
.card-heading { display: flex; padding-bottom: var(--ocop-space-4); align-items: end; justify-content: space-between; border-bottom: 1px solid var(--ocop-border); gap: 15px; }
.card-heading h2 { margin: 3px 0 0; font-size: 17px; }
.card-heading small { color: var(--ocop-slate); font-size: var(--ocop-font-size-caption); }
.edit-button { min-height: 44px; }
dl { display: grid; margin: 0; padding-top: var(--ocop-space-5); grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--ocop-space-5) var(--ocop-space-8); }
dl div { display: grid; gap: var(--ocop-space-1); }
.wide { grid-column: 1 / -1; }
dt { color: var(--ocop-slate); font-size: var(--ocop-font-size-caption); }
dd { margin: 0; color: var(--ocop-navy); font-size: var(--ocop-font-size-small); font-weight: 700; overflow-wrap: anywhere; }
.locked-note { margin: var(--ocop-space-4) 0 0; color: var(--ocop-slate); font-size: var(--ocop-font-size-caption); }
.contact-form { display: grid; padding-top: var(--ocop-space-5); grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--ocop-space-4) var(--ocop-space-5); }
.contact-form .form-control { min-height: 44px; }
.form-actions { display: flex; justify-content: flex-end; gap: var(--ocop-space-3); }
.form-actions button { min-height: 44px; }
.profile-help { display: flex; padding: 18px var(--ocop-space-5); align-items: center; justify-content: space-between; gap: var(--ocop-space-5); }
.profile-help strong { font-size: var(--ocop-font-size-caption); }
.profile-help p { margin-top: var(--ocop-space-1); max-width: 680px; }
@media (max-width: 767.98px) {
  .page-heading, .profile-help { align-items: stretch; flex-direction: column; }
  .account-link, .profile-help a { text-align: center; }
  .summary-card { grid-template-columns: auto 1fr; }
  .review-time { grid-column: 1 / -1; text-align: left; }
  .card-heading { align-items: start; flex-direction: column; }
  dl, .contact-form { grid-template-columns: 1fr; }
  .wide { grid-column: auto; }
  .form-actions { flex-direction: column-reverse; }
}
</style>
