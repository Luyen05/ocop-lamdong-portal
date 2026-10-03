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
.applications-page { display: grid; gap: var(--admin-space-5); font-family: var(--admin-font); }

/* ── Page heading ── */
.page-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--admin-space-4); flex-wrap: wrap; }
.page-heading > div > span { color: var(--admin-primary); font-size: var(--admin-font-xs); font-weight: 800; text-transform: uppercase; letter-spacing: 0.07em; }
.page-heading h1 { margin: 4px 0 4px; font-size: 1.625rem; font-weight: 800; color: var(--admin-text); }
.page-heading p { margin: 0; color: var(--admin-muted); font-size: var(--admin-font-sm); }
.page-heading > strong { padding: 5px 14px; border-radius: var(--admin-radius-pill); background: var(--admin-primary-soft); color: var(--admin-primary); font-size: var(--admin-font-xs); font-weight: 800; }

/* ── Filter bar ── */
.filter-bar {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(160px, 200px) auto;
  gap: 10px;
  padding: var(--admin-space-4);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-lg);
  background: var(--admin-card);
  box-shadow: var(--admin-shadow-sm);
}
.filter-bar label { margin: 0; }
.form-control, .form-select {
  width: 100%;
  height: var(--admin-control-height);
  padding: 0 12px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-card);
  color: var(--admin-text);
  font-size: var(--admin-font-sm);
  outline: none;
  transition: border-color var(--admin-transition);
}
.form-control:focus, .form-select:focus { border-color: var(--admin-primary); }
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 0 16px;
  height: var(--admin-control-height);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  font-size: var(--admin-font-sm);
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--admin-transition);
  background: var(--admin-card);
  color: var(--admin-text);
}
.btn-success { border-color: var(--admin-success); background: var(--admin-success); color: #fff; }
.btn-success:hover { background: #059669; }
.btn-danger { border-color: var(--admin-danger); background: var(--admin-danger); color: #fff; }
.btn-danger:hover { background: #DC2626; }
.btn-light, .btn-sm { background: var(--admin-bg); color: var(--admin-muted); }
.btn-light:hover { border-color: var(--admin-primary); color: var(--admin-primary); }
.btn-outline-danger { border-color: #FECACA; background: transparent; color: var(--admin-danger-text); }
.btn-outline-danger:hover { background: var(--admin-danger-soft); }
.btn:disabled { cursor: not-allowed; opacity: 0.5; }

/* ── Alert ── */
.alert { display: flex; align-items: center; gap: var(--admin-space-3); padding: var(--admin-space-3) var(--admin-space-4); border-radius: var(--admin-radius-md); font-size: var(--admin-font-sm); }
.alert-danger { background: var(--admin-danger-soft); color: var(--admin-danger-text); border: 1px solid #FECACA; }

/* ── Table card ── */
.table-card {
  overflow: hidden;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-lg);
  background: var(--admin-card);
  box-shadow: var(--admin-shadow-sm);
}
.table-responsive { overflow-x: auto; }
.table { width: 100%; border-collapse: collapse; }
.table th {
  padding: 11px 20px;
  background: var(--admin-bg);
  color: var(--admin-muted);
  font-size: var(--admin-font-xs);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
  text-align: left;
  border-bottom: 1px solid var(--admin-border);
}
.table th.text-end { text-align: right; }
.table td {
  padding: 14px 20px;
  font-size: var(--admin-font-sm);
  color: var(--admin-text);
  border-bottom: 1px solid var(--admin-border-soft);
  vertical-align: middle;
}
.table tbody tr:last-child td { border-bottom: 0; }
.table tbody tr:hover td { background: var(--admin-bg); }
.table td strong { display: block; font-weight: 700; }
.table td small { display: block; margin-top: 3px; color: var(--admin-muted); font-size: var(--admin-font-xs); }
.align-middle td { vertical-align: middle; }
.mb-0 { margin-bottom: 0; }
.ms-2 { margin-left: 8px; }

/* ── Status badge ── */
.status-badge { display: inline-flex; padding: 3px 10px; border-radius: var(--admin-radius-pill); font-size: var(--admin-font-xs); font-weight: 700; white-space: nowrap; }
.status-pending { background: var(--admin-badge-pending-bg); color: var(--admin-badge-pending-text); }
.status-approved { background: var(--admin-badge-approved-bg); color: var(--admin-badge-approved-text); }
.status-rejected { background: var(--admin-badge-rejected-bg); color: var(--admin-badge-rejected-text); }

/* ── Row actions ── */
.row-actions { display: flex; justify-content: flex-end; gap: 6px; }
.btn-sm { height: 32px; padding: 0 12px; font-size: var(--admin-font-xs); }

/* ── State row ── */
.state-row { display: flex; min-height: 200px; align-items: center; justify-content: center; gap: 10px; color: var(--admin-muted); font-size: var(--admin-font-base); }
.spinner-border { display: inline-block; width: 20px; height: 20px; border: 3px solid var(--admin-border); border-top-color: var(--admin-primary); border-radius: 50%; animation: spin 0.7s linear infinite; }
.spinner-border-sm { width: 16px; height: 16px; border-width: 2px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Pagination ── */
.pagination-bar { display: flex; align-items: center; justify-content: flex-end; gap: var(--admin-space-3); padding: var(--admin-space-3) 0; color: var(--admin-muted); font-size: var(--admin-font-sm); font-weight: 600; }

/* ── Modal ── */
.modal-layer { position: fixed; z-index: 200; inset: 0; display: grid; padding: var(--admin-space-5); place-items: center; overflow-y: auto; background: rgba(30, 42, 71, 0.55); backdrop-filter: blur(4px); }
.moderation-dialog {
  width: min(100%, 720px);
  max-height: calc(100vh - 40px);
  padding: var(--admin-space-6);
  overflow-y: auto;
  border-radius: var(--admin-radius-lg);
  background: var(--admin-card);
  box-shadow: var(--admin-shadow-modal);
}
.moderation-dialog header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--admin-space-4); padding-bottom: var(--admin-space-4); border-bottom: 1px solid var(--admin-border-soft); }
.moderation-dialog header span { color: var(--admin-primary); font-size: var(--admin-font-xs); font-weight: 800; text-transform: uppercase; letter-spacing: 0.06em; }
.moderation-dialog h2 { margin: 3px 0 0; font-size: var(--admin-font-2xl); color: var(--admin-text); }
.moderation-dialog header button { display: grid; width: 32px; height: 32px; place-items: center; border: 0; border-radius: var(--admin-radius-sm); background: var(--admin-bg); color: var(--admin-muted); cursor: pointer; }
.moderation-dialog header button:hover { color: var(--admin-danger); background: var(--admin-danger-soft); }

.detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px 22px; margin: var(--admin-space-5) 0; padding: var(--admin-space-4); border-radius: var(--admin-radius-md); background: var(--admin-bg); }
.detail-grid div { display: grid; gap: 3px; }
.detail-grid dt { color: var(--admin-muted); font-size: var(--admin-font-xs); font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }
.detail-grid dd { margin: 0; font-size: var(--admin-font-sm); font-weight: 600; color: var(--admin-text); }
.full-row { grid-column: 1 / -1; }

.moderation-dialog form label { display: grid; gap: 6px; color: var(--admin-muted); font-size: var(--admin-font-xs); font-weight: 700; }
.moderation-dialog form label span { color: var(--admin-muted); font-size: var(--admin-font-xs); font-weight: 700; text-transform: uppercase; }
.moderation-dialog form .form-control { height: auto; padding: 10px 12px; resize: vertical; }
.dialog-actions { display: flex; justify-content: flex-end; gap: var(--admin-space-2); margin-top: var(--admin-space-4); padding-top: var(--admin-space-4); border-top: 1px solid var(--admin-border-soft); }

.reviewed-message { padding: var(--admin-space-4); border-radius: var(--admin-radius-md); background: var(--admin-bg); color: var(--admin-text); }
.reviewed-message p { margin: 4px 0 0; color: var(--admin-muted); font-size: var(--admin-font-sm); }
.py-2 { padding-top: 8px; padding-bottom: 8px; }

@media (max-width: 767.98px) {
  .page-heading { align-items: flex-start; flex-direction: column; }
  .filter-bar { grid-template-columns: 1fr; }
  .detail-grid { grid-template-columns: 1fr; }
  .full-row { grid-column: auto; }
}
</style>
