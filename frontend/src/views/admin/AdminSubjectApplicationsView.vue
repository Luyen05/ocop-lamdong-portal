<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import { useDialogFocus } from '@/composables/useDialogFocus'
import { getApiErrorMessage } from '@/services/api-error'
import {
  listSubjectApplications,
  moderateSubjectApplication,
} from '@/services/subjects'
import type {
  AdminSubjectApplication,
  SubjectStatus,
  SubjectType,
} from '@/types/subject'

const applications = ref<AdminSubjectApplication[]>([])
const page = ref(1)
const pageSize = 10
const total = ref(0)
const isLoading = ref(false)
const errorMessage = ref('')
const selectedApplication = ref<AdminSubjectApplication | null>(null)
const moderationStatus = ref<'approved' | 'rejected'>('approved')
const moderationNote = ref('')
const isModerating = ref(false)
const moderationError = ref('')
const moderationDialog = ref<HTMLElement | null>(null)

const filters = reactive<{ search: string; status: SubjectStatus | '' }>({
  search: '',
  status: 'pending',
})

const statusLabels: Record<SubjectStatus, string> = {
  pending: 'Chờ duyệt',
  approved: 'Đã duyệt',
  rejected: 'Từ chối',
}

const typeLabels: Record<SubjectType, string> = {
  cooperative: 'Hợp tác xã',
  enterprise: 'Doanh nghiệp',
  household: 'Hộ kinh doanh',
  individual: 'Cá nhân / cơ sở sản xuất',
}

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const isModerationDialogOpen = computed(() => Boolean(selectedApplication.value))

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('vi-VN', {
    dateStyle: 'short',
    timeStyle: 'short',
  }).format(new Date(value))
}

async function loadApplications(): Promise<void> {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await listSubjectApplications({
      page: page.value,
      page_size: pageSize,
      search: filters.search.trim() || undefined,
      status: filters.status || undefined,
    })
    applications.value = response.items
    total.value = response.total
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải danh sách hồ sơ.')
  } finally {
    isLoading.value = false
  }
}

function applyFilters(): void {
  page.value = 1
  void loadApplications()
}

function changePage(nextPage: number): void {
  page.value = Math.min(Math.max(nextPage, 1), totalPages.value)
  void loadApplications()
}

function openModeration(
  application: AdminSubjectApplication,
  status: 'approved' | 'rejected',
): void {
  selectedApplication.value = application
  moderationStatus.value = status
  moderationNote.value = ''
  moderationError.value = ''
}

function closeModeration(): void {
  if (isModerating.value) return
  selectedApplication.value = null
}

useDialogFocus(isModerationDialogOpen, moderationDialog, closeModeration)

async function submitModeration(): Promise<void> {
  if (!selectedApplication.value || isModerating.value) return
  moderationError.value = ''
  if (moderationStatus.value === 'rejected' && !moderationNote.value.trim()) {
    moderationError.value = 'Vui lòng nhập lý do từ chối để người dùng bổ sung hồ sơ.'
    return
  }

  isModerating.value = true
  try {
    await moderateSubjectApplication(selectedApplication.value.id, {
      status: moderationStatus.value,
      note: moderationNote.value.trim() || null,
    })
    selectedApplication.value = null
    await loadApplications()
  } catch (error) {
    moderationError.value = getApiErrorMessage(error, 'Không thể cập nhật hồ sơ.')
  } finally {
    isModerating.value = false
  }
}

onMounted(loadApplications)
</script>

<template>
  <main class="applications-page">
    <header class="page-heading">
      <div>
        <span>Kiểm duyệt chủ thể</span>
        <h1>Hồ sơ đăng ký chủ thể</h1>
        <p>Xác minh đơn vị trước khi cấp quyền quản lý sản phẩm và điểm du lịch.</p>
      </div>
      <strong>{{ total }} hồ sơ</strong>
    </header>

    <form class="filter-bar" @submit.prevent="applyFilters">
      <label>
        <span class="visually-hidden">Tìm hồ sơ</span>
        <input
          v-model="filters.search"
          class="form-control"
          type="search"
          placeholder="Tên đơn vị, người đăng ký, email..."
        />
      </label>
      <label>
        <span class="visually-hidden">Trạng thái</span>
        <select v-model="filters.status" class="form-select" @change="applyFilters">
          <option value="">Tất cả trạng thái</option>
          <option value="pending">Chờ duyệt</option>
          <option value="approved">Đã duyệt</option>
          <option value="rejected">Đã từ chối</option>
        </select>
      </label>
      <button class="btn btn-success" type="submit">Tìm kiếm</button>
    </form>

    <div v-if="errorMessage" class="alert alert-danger" role="alert">
      {{ errorMessage }}
      <button class="btn btn-sm btn-outline-danger ms-2" type="button" @click="loadApplications">
        Thử lại
      </button>
    </div>

    <section class="table-card">
      <div v-if="isLoading" class="state-row" aria-live="polite">
        <span class="spinner-border spinner-border-sm" aria-hidden="true" />
        Đang tải hồ sơ...
      </div>
      <div v-else-if="applications.length === 0" class="state-row">
        Không có hồ sơ phù hợp với bộ lọc.
      </div>
      <div v-else class="table-responsive">
        <table class="table align-middle mb-0">
          <thead>
            <tr>
              <th>Đơn vị</th>
              <th>Người đăng ký</th>
              <th>Khu vực</th>
              <th>Ngày gửi</th>
              <th>Trạng thái</th>
              <th class="text-end">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="application in applications" :key="application.id">
              <td>
                <strong>{{ application.name }}</strong>
                <small>{{ typeLabels[application.type] }} · MST: {{ application.tax_code || '—' }}</small>
              </td>
              <td>
                <span>{{ application.applicant.full_name }}</span>
                <small>{{ application.applicant.email }}</small>
              </td>
              <td>{{ application.district }}</td>
              <td>{{ formatDate(application.created_at) }}</td>
              <td>
                <span class="status-badge" :class="`status-${application.status}`">
                  {{ statusLabels[application.status] }}
                </span>
              </td>
              <td>
                <div v-if="application.status === 'pending'" class="row-actions">
                  <button
                    class="btn btn-sm btn-outline-danger"
                    type="button"
                    @click="openModeration(application, 'rejected')"
                  >
                    Từ chối
                  </button>
                  <button
                    class="btn btn-sm btn-success"
                    type="button"
                    @click="openModeration(application, 'approved')"
                  >
                    Duyệt
                  </button>
                </div>
                <button
                  v-else
                  class="btn btn-sm btn-light"
                  type="button"
                  @click="openModeration(application, application.status === 'approved' ? 'approved' : 'rejected')"
                >
                  Xem chi tiết
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <nav v-if="totalPages > 1" class="pagination-bar" aria-label="Phân trang hồ sơ">
      <button class="btn btn-sm btn-light" type="button" :disabled="page === 1" @click="changePage(page - 1)">
        Trước
      </button>
      <span>Trang {{ page }} / {{ totalPages }}</span>
      <button class="btn btn-sm btn-light" type="button" :disabled="page === totalPages" @click="changePage(page + 1)">
        Sau
      </button>
    </nav>

    <div v-if="selectedApplication" class="modal-layer" role="presentation" @click.self="closeModeration">
      <section
        ref="moderationDialog"
        class="moderation-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="moderation-title"
        tabindex="-1"
      >
        <header>
          <div>
            <span>Hồ sơ #{{ selectedApplication.id }}</span>
            <h2 id="moderation-title">{{ selectedApplication.name }}</h2>
          </div>
          <button type="button" aria-label="Đóng" @click="closeModeration"><AppIcon name="close" :size="17" /></button>
        </header>

        <dl class="detail-grid">
          <div><dt>Loại hình</dt><dd>{{ typeLabels[selectedApplication.type] }}</dd></div>
          <div><dt>Người đại diện</dt><dd>{{ selectedApplication.representative }}</dd></div>
          <div><dt>Số điện thoại</dt><dd>{{ selectedApplication.phone }}</dd></div>
          <div><dt>Email</dt><dd>{{ selectedApplication.email || '—' }}</dd></div>
          <div><dt>Mã số thuế</dt><dd>{{ selectedApplication.tax_code || '—' }}</dd></div>
          <div><dt>Tài khoản gửi</dt><dd>{{ selectedApplication.applicant.email }}</dd></div>
          <div class="full-row"><dt>Địa chỉ</dt><dd>{{ selectedApplication.address }}</dd></div>
        </dl>

        <div v-if="selectedApplication.status !== 'pending'" class="reviewed-message">
          <strong>{{ statusLabels[selectedApplication.status] }}</strong>
          <p>{{ selectedApplication.moderation_note || 'Không có ghi chú kiểm duyệt.' }}</p>
        </div>

        <form v-else @submit.prevent="submitModeration">
          <div v-if="moderationError" class="alert alert-danger py-2" role="alert">
            {{ moderationError }}
          </div>
          <label v-if="moderationStatus === 'rejected'">
            <span>Lý do từ chối *</span>
            <textarea
              v-model.trim="moderationNote"
              class="form-control"
              rows="3"
              maxlength="1000"
              placeholder="Nêu rõ thông tin người dùng cần bổ sung..."
              required
            />
          </label>
          <label v-else>
            <span>Ghi chú duyệt (không bắt buộc)</span>
            <textarea v-model.trim="moderationNote" class="form-control" rows="2" maxlength="1000" />
          </label>
          <div class="dialog-actions">
            <button class="btn btn-light" type="button" @click="closeModeration">Hủy</button>
            <button
              class="btn"
              :class="moderationStatus === 'approved' ? 'btn-success' : 'btn-danger'"
              type="submit"
              :disabled="isModerating"
            >
              {{ isModerating ? 'Đang xử lý...' : moderationStatus === 'approved' ? 'Xác nhận duyệt' : 'Xác nhận từ chối' }}
            </button>
          </div>
        </form>
      </section>
    </div>
  </main>
</template>

<style scoped>
.applications-page { display: grid; gap: var(--ocop-space-5); }
.page-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--ocop-space-5); }
.page-heading > div > span { color: var(--ocop-primary-700); font-size: var(--ocop-font-size-xs); font-weight: 800; text-transform: uppercase; }
.page-heading h1 { margin: var(--ocop-space-1) 0; font-size: clamp(25px, 3vw, 34px); font-weight: 800; }
.page-heading p { margin: 0; color: var(--ocop-slate); }
.page-heading > strong { padding: var(--ocop-space-2) var(--ocop-space-3); border-radius: var(--ocop-radius-pill); background: var(--ocop-mint-soft); color: var(--ocop-primary-900); font-size: var(--ocop-font-size-caption); }
.filter-bar { display: grid; grid-template-columns: minmax(220px, 1fr) minmax(170px, 220px) auto; gap: 10px; padding: var(--ocop-space-4); border: 1px solid var(--ocop-border); border-radius: 14px; background: var(--ocop-card); }
.filter-bar label { margin: 0; }
.table-card { overflow: hidden; border: 1px solid var(--ocop-border); border-radius: 14px; background: var(--ocop-card); }
.table th { padding: 13px var(--ocop-space-4); background: var(--ocop-surface-muted); color: var(--ocop-slate); font-size: var(--ocop-font-size-xs); text-transform: uppercase; white-space: nowrap; }
.table td { padding: 15px var(--ocop-space-4); font-size: var(--ocop-font-size-small); }
.table td strong,
.table td small { display: block; }
.table td small { margin-top: 3px; color: var(--ocop-slate); font-size: var(--ocop-font-size-xs); }
.status-badge { display: inline-flex; padding: 5px 9px; border-radius: var(--ocop-radius-pill); font-size: var(--ocop-font-size-2xs); font-weight: 800; white-space: nowrap; }
.status-pending { background: var(--ocop-warning-soft); color: var(--ocop-warning); }
.status-approved { background: var(--ocop-success-soft); color: var(--ocop-success); }
.status-rejected { background: var(--ocop-danger-soft); color: var(--ocop-danger); }
.row-actions { display: flex; justify-content: flex-end; gap: 6px; }
.state-row { display: flex; min-height: 180px; align-items: center; justify-content: center; gap: 10px; color: var(--ocop-slate); }
.pagination-bar { display: flex; align-items: center; justify-content: flex-end; gap: var(--ocop-space-3); color: var(--ocop-slate); font-size: var(--ocop-font-size-caption); }
.modal-layer { position: fixed; z-index: 200; inset: 0; display: grid; padding: var(--ocop-space-5); place-items: center; overflow-y: auto; background: color-mix(in srgb, var(--ocop-neutral-900) 58%, transparent); }
.moderation-dialog { width: min(100%, 720px); max-height: calc(100vh - 40px); padding: var(--ocop-space-6); overflow-y: auto; border-radius: 18px; background: var(--ocop-card); box-shadow: 0 28px 70px color-mix(in srgb, var(--ocop-neutral-900) 30%, transparent); }
.moderation-dialog header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--ocop-space-5); }
.moderation-dialog header span { color: var(--ocop-primary-700); font-size: var(--ocop-font-size-xs); font-weight: 800; }
.moderation-dialog h2 { margin: 3px 0 0; font-size: 23px; }
.moderation-dialog header button { border: 0; background: transparent; color: var(--ocop-slate); font-size: 28px; line-height: 1; }
.detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px 22px; margin: var(--ocop-space-6) 0; padding: 18px; border-radius: var(--ocop-radius-md); background: var(--ocop-surface); }
.detail-grid div { display: grid; gap: 3px; }
.detail-grid dt,
.moderation-dialog form label span { color: var(--ocop-slate); font-size: var(--ocop-font-size-xs); font-weight: 700; }
.detail-grid dd { margin: 0; font-size: var(--ocop-font-size-small); font-weight: 650; }
.full-row { grid-column: 1 / -1; }
.moderation-dialog form label { display: grid; gap: 7px; }
.dialog-actions { display: flex; justify-content: flex-end; gap: var(--ocop-space-2); margin-top: 18px; }
.reviewed-message { padding: var(--ocop-space-4); border-radius: 10px; background: var(--ocop-surface-muted); }
.reviewed-message p { margin: var(--ocop-space-1) 0 0; }
@media (max-width: 767.98px) {
  .page-heading { align-items: flex-start; flex-direction: column; }
  .filter-bar { grid-template-columns: 1fr; }
  .detail-grid { grid-template-columns: 1fr; }
  .full-row { grid-column: auto; }
}
</style>
