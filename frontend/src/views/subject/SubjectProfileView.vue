<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { getApiErrorMessage } from '@/services/api-error'
import { getMySubjectApplication } from '@/services/subjects'
import type { SubjectApplication } from '@/types/subject'

const subject = ref<SubjectApplication | null>(null)
const loading = ref(true)
const errorMessage = ref('')

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

async function loadProfile(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    subject.value = await getMySubjectApplication()
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải hồ sơ chủ thể.')
  } finally {
    loading.value = false
  }
}

onMounted(loadProfile)
</script>

<template>
  <main class="profile-page">
    <header class="page-heading">
      <div>
        <span>THÔNG TIN ĐƠN VỊ</span>
        <h1>Hồ sơ chủ thể</h1>
        <p>Thông tin đã được quản trị viên xác minh để cấp quyền quản lý sản phẩm.</p>
      </div>
      <RouterLink class="account-link" to="/tai-khoan">Sửa thông tin tài khoản</RouterLink>
    </header>

    <div v-if="errorMessage" class="alert alert-danger error-card" role="alert">
      <span>{{ errorMessage }}</span>
      <button type="button" @click="loadProfile">Thử lại</button>
    </div>
    <div v-if="loading" class="state-card" role="status">Đang tải hồ sơ...</div>

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
        <RouterLink v-if="subject.status === 'rejected'" to="/dang-ky-chu-the">
          Bổ sung và gửi lại hồ sơ
        </RouterLink>
      </section>

      <section class="details-card">
        <div class="card-heading">
          <div><span>HỒ SƠ PHÁP LÝ</span><h2>Thông tin chủ thể</h2></div>
          <small v-if="subject.status === 'approved'">Hồ sơ đã duyệt chỉ được xem</small>
        </div>
        <dl>
          <div><dt>Loại hình</dt><dd>{{ typeLabels[subject.type] }}</dd></div>
          <div><dt>Mã số thuế</dt><dd>{{ subject.tax_code || 'Chưa cung cấp' }}</dd></div>
          <div><dt>Người đại diện</dt><dd>{{ subject.representative }}</dd></div>
          <div><dt>Số điện thoại</dt><dd>{{ subject.phone }}</dd></div>
          <div><dt>Email đơn vị</dt><dd>{{ subject.email || 'Chưa cung cấp' }}</dd></div>
          <div><dt>Khu vực</dt><dd>{{ subject.district }}</dd></div>
          <div class="wide"><dt>Địa chỉ</dt><dd>{{ subject.address }}</dd></div>
        </dl>
      </section>

      <aside class="profile-help">
        <div>
          <strong>Cần thay đổi thông tin đơn vị?</strong>
          <p>Trong phiên bản đầu, hồ sơ đã duyệt được khóa để tránh sai lệch thông tin xác minh. Hãy liên hệ quản trị viên khi tên đơn vị, mã số thuế hoặc địa chỉ thay đổi.</p>
        </div>
        <RouterLink to="/">Về trang công khai</RouterLink>
      </aside>
    </template>
  </main>
</template>

<style scoped>
.profile-page { display: grid; max-width: 980px; margin-inline: auto; gap: 18px; }
.page-heading { display: flex; align-items: end; justify-content: space-between; gap: 20px; }
.page-heading span, .card-heading span { color: var(--ocop-primary-700); font-size: 10px; font-weight: 800; letter-spacing: .05em; }
.page-heading h1 { margin: 4px 0; color: var(--ocop-navy); font-size: 30px; }
.page-heading p { margin: 0; color: var(--ocop-slate); font-size: 13px; }
.account-link, .profile-help a { padding: 10px 14px; border: 1px solid var(--ocop-primary-700); border-radius: 9px; color: var(--ocop-primary-700); font-size: 11px; font-weight: 750; text-decoration: none; white-space: nowrap; }
.state-card, .summary-card, .details-card, .review-note, .profile-help { border: 1px solid var(--ocop-border); border-radius: 14px; background: #fff; }
.state-card { padding: 28px; color: var(--ocop-slate); text-align: center; }
.error-card { display: flex; margin: 0; align-items: center; justify-content: space-between; gap: 12px; }
.error-card button { border: 0; background: transparent; color: inherit; font-weight: 750; text-decoration: underline; }
.summary-card { display: grid; padding: 22px; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 16px; }
.subject-mark { display: grid; width: 54px; height: 54px; place-items: center; border-radius: 14px; background: #e4f4ed; color: var(--ocop-primary-700); font-size: 22px; font-weight: 800; }
.status-badge { display: inline-flex; width: fit-content; padding: 3px 8px; border-radius: 999px; background: #fff5d8; color: #8a5b00; font-size: 9px; font-weight: 800; text-transform: uppercase; }
.status-approved { background: var(--ocop-success-soft); color: var(--ocop-success); }
.status-rejected { background: var(--ocop-danger-soft); color: var(--ocop-danger); }
.subject-name h2 { margin: 5px 0 2px; color: var(--ocop-navy); font-size: 20px; }
.subject-name p, .review-note p, .profile-help p { margin: 0; color: var(--ocop-slate); font-size: 12px; }
.review-time { display: grid; text-align: right; }
.review-time small { color: var(--ocop-slate); font-size: 9px; }
.review-time strong { font-size: 11px; }
.review-note { padding: 17px 20px; border-color: #e8cf98; background: var(--ocop-warning-soft); }
.review-note strong { color: var(--ocop-warning); font-size: 12px; }
.review-note p { margin: 5px 0 10px; color: var(--ocop-warning); }
.review-note a { color: #76520a; font-size: 11px; font-weight: 750; }
.details-card { padding: 22px; }
.card-heading { display: flex; padding-bottom: 16px; align-items: end; justify-content: space-between; border-bottom: 1px solid var(--ocop-border); gap: 15px; }
.card-heading h2 { margin: 3px 0 0; font-size: 17px; }
.card-heading small { color: var(--ocop-slate); font-size: 10px; }
dl { display: grid; margin: 0; padding-top: 20px; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px 32px; }
dl div { display: grid; gap: 4px; }
dl .wide { grid-column: 1 / -1; }
dt { color: var(--ocop-slate); font-size: 10px; }
dd { margin: 0; color: var(--ocop-navy); font-size: 13px; font-weight: 700; overflow-wrap: anywhere; }
.profile-help { display: flex; padding: 18px 20px; align-items: center; justify-content: space-between; gap: 20px; }
.profile-help strong { font-size: 12px; }
.profile-help p { margin-top: 4px; max-width: 680px; }
@media (max-width: 767.98px) {
  .page-heading, .profile-help { align-items: stretch; flex-direction: column; }
  .account-link, .profile-help a { text-align: center; }
  .summary-card { grid-template-columns: auto 1fr; }
  .review-time { grid-column: 1 / -1; text-align: left; }
  .card-heading { align-items: start; flex-direction: column; }
  dl { grid-template-columns: 1fr; }
  dl .wide { grid-column: auto; }
}
</style>
