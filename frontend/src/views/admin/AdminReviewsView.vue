<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

import ReviewStars from '@/components/reviews/ReviewStars.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import StatusPanel from '@/components/ui/StatusPanel.vue'
import { useDialogFocus } from '@/composables/useDialogFocus'
import { getApiErrorMessage } from '@/services/api-error'
import { listAdminReviews, moderateReview } from '@/services/reviews'
import type { AdminReview, ReviewStatus, ReviewTargetType } from '@/types/review'
import { formatReviewDate, reviewTargetLink, reviewTargetTypeLabel } from '@/utils/review'

const PAGE_SIZE = 10

const reviews = ref<AdminReview[]>([])
const page = ref(1)
const total = ref(0)
const isLoading = ref(false)
const errorMessage = ref('')
const notice = ref('')
const approvingId = ref<number | null>(null)
const actionError = ref('')

const filters = reactive<{ status: ReviewStatus | ''; target: ReviewTargetType | ''; q: string }>({
  status: 'pending',
  target: '',
  q: '',
})

const rejecting = ref<AdminReview | null>(null)
const rejectReason = ref('')
const rejectError = ref('')
const isRejecting = ref(false)
const rejectDialog = ref<HTMLElement | null>(null)
const isRejectDialogOpen = computed(() => Boolean(rejecting.value))

const statusLabels: Record<ReviewStatus, string> = {
  pending: 'Chờ duyệt',
  approved: 'Đã duyệt',
  rejected: 'Từ chối',
}

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

// Lọc nhanh liên tục: chỉ nhận kết quả của lần gọi mới nhất.
let requestId = 0

async function loadReviews(): Promise<void> {
  const current = ++requestId
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await listAdminReviews({
      page: page.value,
      page_size: PAGE_SIZE,
      status: filters.status || undefined,
      target: filters.target || undefined,
      q: filters.q.trim() || undefined,
    })
    if (current !== requestId) return
    reviews.value = response.items
    total.value = response.total
  } catch (error) {
    if (current !== requestId) return
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải danh sách đánh giá.')
  } finally {
    if (current === requestId) isLoading.value = false
  }
}

function applyFilters(): void {
  page.value = 1
  notice.value = ''
  void loadReviews()
}

function changePage(nextPage: number): void {
  page.value = Math.min(Math.max(nextPage, 1), totalPages.value)
  void loadReviews()
}

async function afterModeration(message: string): Promise<void> {
  notice.value = message
  // Trang cuối có thể trống sau khi duyệt hết: lùi một trang.
  if (reviews.value.length === 1 && page.value > 1 && filters.status) page.value -= 1
  await loadReviews()
}

async function approve(review: AdminReview): Promise<void> {
  if (approvingId.value !== null) return
  approvingId.value = review.id
  actionError.value = ''
  notice.value = ''
  try {
    await moderateReview(review.id, { action: 'approve' })
    await afterModeration(`Đã duyệt đánh giá của ${review.author.full_name}.`)
  } catch (error) {
    actionError.value = getApiErrorMessage(error, 'Không thể duyệt đánh giá.')
  } finally {
    approvingId.value = null
  }
}

function openReject(review: AdminReview): void {
  rejecting.value = review
  rejectReason.value = ''
  rejectError.value = ''
  actionError.value = ''
}

function closeReject(): void {
  if (isRejecting.value) return
  rejecting.value = null
}

useDialogFocus(isRejectDialogOpen, rejectDialog, closeReject)

async function submitReject(): Promise<void> {
  if (!rejecting.value || isRejecting.value) return
  const reason = rejectReason.value.trim()
  if (!reason) {
    rejectError.value = 'Vui lòng nhập lý do từ chối để người viết biết cần sửa gì.'
    return
  }
  isRejecting.value = true
  rejectError.value = ''
  const review = rejecting.value
  try {
    await moderateReview(review.id, { action: 'reject', reason })
    isRejecting.value = false
    rejecting.value = null
    notice.value = ''
    await afterModeration(`Đã từ chối đánh giá của ${review.author.full_name}.`)
  } catch (error) {
    rejectError.value = getApiErrorMessage(error, 'Không thể từ chối đánh giá.')
  } finally {
    isRejecting.value = false
  }
}

onMounted(loadReviews)
onUnmounted(() => {
  requestId++
})
</script>

<template>
  <div class="reviews-page">
    <header class="page-heading">
      <div>
        <span>Kiểm duyệt nội dung</span>
        <h1>Đánh giá của người dùng</h1>
        <p>Đánh giá chỉ hiển thị công khai sau khi được duyệt. Từ chối cần nêu lý do để người viết sửa lại.</p>
      </div>
      <strong>{{ total }} đánh giá</strong>
    </header>

    <form class="filter-bar" role="search" @submit.prevent="applyFilters">
      <label>
        <span class="filter-label">Tìm kiếm</span>
        <input
          v-model="filters.q"
          class="form-control"
          type="search"
          maxlength="150"
          placeholder="Nội dung, người viết, sản phẩm, điểm du lịch..."
        />
      </label>
      <label>
        <span class="filter-label">Trạng thái</span>
        <select v-model="filters.status" class="form-select" data-test="status-filter" @change="applyFilters">
          <option value="pending">Chờ duyệt</option>
          <option value="approved">Đã duyệt</option>
          <option value="rejected">Đã từ chối</option>
          <option value="">Tất cả trạng thái</option>
        </select>
      </label>
      <label>
        <span class="filter-label">Loại</span>
        <select v-model="filters.target" class="form-select" data-test="target-filter" @change="applyFilters">
          <option value="">Sản phẩm và điểm du lịch</option>
          <option value="product">Sản phẩm OCOP</option>
          <option value="location">Điểm du lịch</option>
        </select>
      </label>
      <button class="btn btn-success" type="submit">Tìm kiếm</button>
    </form>

    <p v-if="notice" class="alert alert-success" role="status">{{ notice }}</p>
    <p v-if="actionError" class="alert alert-danger" role="alert">{{ actionError }}</p>

    <section class="table-card" aria-label="Danh sách đánh giá">
      <StatusPanel v-if="isLoading" kind="loading" :rows="3" message="Đang tải đánh giá…" />
      <StatusPanel v-else-if="errorMessage" kind="error" :message="errorMessage" @retry="loadReviews" />
      <StatusPanel
        v-else-if="reviews.length === 0"
        kind="empty"
        :title="filters.status === 'pending' && !filters.q && !filters.target ? 'Không còn đánh giá chờ duyệt' : 'Không có đánh giá phù hợp với bộ lọc'"
        message="Đổi trạng thái, loại hoặc từ khóa để xem đánh giá khác."
      />
      <div v-else class="table-responsive">
        <table class="table">
          <thead>
            <tr>
              <th scope="col">Nội dung</th>
              <th scope="col">Đối tượng</th>
              <th scope="col">Người viết</th>
              <th scope="col">Trạng thái</th>
              <th scope="col" class="text-end">Thao tác</th>
            </tr>
          </thead>
          <tbody class="stagger-in">
            <tr v-for="review in reviews" :key="review.id" :data-test="`row-${review.id}`">
              <td class="comment-cell">
                <ReviewStars :rating="review.rating" size="sm" />
                <p class="comment-text">{{ review.comment }}</p>
                <small>Gửi {{ formatReviewDate(review.created_at) }}<template v-if="review.updated_at !== review.created_at"> · sửa {{ formatReviewDate(review.updated_at) }}</template></small>
              </td>
              <td>
                <small>{{ reviewTargetTypeLabel(review.target) }}</small>
                <RouterLink class="target-link" :to="reviewTargetLink(review.target)" target="_blank" rel="noopener">
                  {{ review.target.name }}<span class="visually-hidden"> (mở trong thẻ mới)</span>
                </RouterLink>
              </td>
              <td>
                <strong>{{ review.author.full_name }}</strong>
                <small>{{ review.author.email }}</small>
              </td>
              <td>
                <span class="status-badge" :class="`status-${review.status}`">{{ statusLabels[review.status] }}</span>
                <small v-if="review.status === 'rejected' && review.rejection_reason" class="reason">
                  Lý do: {{ review.rejection_reason }}
                </small>
                <small v-if="review.reviewed_by_name && review.status !== 'pending'">bởi {{ review.reviewed_by_name }}</small>
              </td>
              <td>
                <div class="row-actions">
                  <button
                    v-if="review.status !== 'rejected'"
                    class="btn btn-outline-danger"
                    type="button"
                    data-test="reject"
                    :disabled="approvingId !== null"
                    @click="openReject(review)"
                  >
                    {{ review.status === 'approved' ? 'Gỡ' : 'Từ chối' }}<span class="visually-hidden"> đánh giá của {{ review.author.full_name }}</span>
                  </button>
                  <button
                    v-if="review.status !== 'approved'"
                    class="btn btn-success"
                    type="button"
                    data-test="approve"
                    :disabled="approvingId !== null"
                    @click="approve(review)"
                  >
                    {{ approvingId === review.id ? 'Đang duyệt…' : 'Duyệt' }}<span class="visually-hidden"> đánh giá của {{ review.author.full_name }}</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <nav v-if="totalPages > 1" class="pagination-bar" aria-label="Phân trang đánh giá">
      <button class="btn btn-light" type="button" :disabled="page === 1 || isLoading" @click="changePage(page - 1)">Trước</button>
      <span>Trang {{ page }} / {{ totalPages }}</span>
      <button class="btn btn-light" type="button" :disabled="page === totalPages || isLoading" @click="changePage(page + 1)">Sau</button>
    </nav>

    <Transition name="ocop-fade">
      <div v-if="rejecting" class="modal-layer" role="presentation" @click.self="closeReject">
        <section
          ref="rejectDialog"
          class="moderation-dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="reject-title"
          tabindex="-1"
        >
          <header>
            <div>
              <span>Đánh giá #{{ rejecting.id }}</span>
              <h2 id="reject-title">{{ rejecting.status === 'approved' ? 'Gỡ đánh giá đang hiển thị' : 'Từ chối đánh giá' }}</h2>
            </div>
            <button type="button" aria-label="Đóng" @click="closeReject"><AppIcon name="close" :size="17" /></button>
          </header>

          <div class="quoted-review">
            <ReviewStars :rating="rejecting.rating" size="sm" />
            <p>{{ rejecting.comment }}</p>
            <small>{{ rejecting.author.full_name }} · {{ rejecting.target.name }}</small>
          </div>

          <form @submit.prevent="submitReject">
            <p v-if="rejectError" class="alert alert-danger" role="alert">{{ rejectError }}</p>
            <label for="reject-reason">
              <span>Lý do từ chối <span aria-hidden="true">*</span></span>
            </label>
            <textarea
              id="reject-reason"
              v-model="rejectReason"
              class="form-control"
              rows="3"
              maxlength="1000"
              aria-describedby="reject-hint"
              placeholder="Ví dụ: Nội dung không liên quan tới sản phẩm, có thông tin quảng cáo..."
            />
            <p id="reject-hint" class="hint">Người viết sẽ thấy lý do này và có thể sửa lại đánh giá.</p>
            <div class="dialog-actions">
              <button class="btn btn-light" type="button" :disabled="isRejecting" @click="closeReject">Hủy</button>
              <button class="btn btn-danger" type="submit" :disabled="isRejecting" data-test="confirm-reject">
                {{ isRejecting ? 'Đang xử lý…' : 'Xác nhận từ chối' }}
              </button>
            </div>
          </form>
        </section>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.reviews-page { display: grid; gap: var(--admin-space-5); font-family: var(--admin-font); }

/* ── Tiêu đề trang (giống trang hồ sơ chủ thể) ── */
.page-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--admin-space-4); flex-wrap: wrap; }
.page-heading > div > span { color: var(--admin-primary); font-size: var(--admin-font-xs); font-weight: 800; text-transform: uppercase; letter-spacing: 0.07em; }
.page-heading h1 { margin: var(--admin-space-1) 0; font-size: var(--admin-font-2xl); font-weight: 800; color: var(--admin-text); }
.page-heading p { margin: 0; color: var(--admin-muted); font-size: var(--admin-font-sm); }
.page-heading > strong { padding: var(--admin-space-1) var(--admin-space-3); border-radius: var(--admin-radius-pill); background: var(--admin-primary-soft); color: var(--admin-primary-dark); font-size: var(--admin-font-xs); font-weight: 800; }

/* ── Bộ lọc ── */
.filter-bar {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(150px, 190px) minmax(170px, 220px) auto;
  align-items: end;
  gap: var(--admin-space-3);
  padding: var(--admin-space-4);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-lg);
  background: var(--admin-card);
  box-shadow: var(--admin-shadow-sm);
}
.filter-bar label { display: grid; gap: var(--admin-space-1); margin: 0; }
.filter-label { color: var(--admin-muted); font-size: var(--admin-font-xs); font-weight: 700; }
.form-control, .form-select {
  width: 100%;
  height: var(--admin-control-height);
  padding: 0 var(--admin-space-3);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background-color: var(--admin-card);
  color: var(--admin-text);
  font-size: var(--admin-font-sm);
  transition: border-color var(--admin-transition);
}
.form-control:focus, .form-select:focus { border-color: var(--admin-primary); outline: 3px solid var(--admin-primary-border); outline-offset: 0; }

/* ── Nút (vùng chạm 44px) ── */
.btn {
  display: inline-flex;
  min-height: var(--admin-control-height);
  align-items: center;
  justify-content: center;
  gap: var(--admin-space-1);
  padding: 0 var(--admin-space-4);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-card);
  color: var(--admin-text);
  font-size: var(--admin-font-sm);
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: background var(--admin-transition), border-color var(--admin-transition), color var(--admin-transition);
}
.btn:focus-visible, .target-link:focus-visible, .moderation-dialog header button:focus-visible { outline: 3px solid var(--admin-primary); outline-offset: 2px; }
.btn-success { border-color: var(--admin-success); background: var(--admin-success); color: var(--ocop-white); }
.btn-success:hover { background: var(--admin-success-hover); }
.btn-danger { border-color: var(--admin-danger); background: var(--admin-danger); color: var(--ocop-white); }
.btn-danger:hover { background: var(--admin-danger-hover); }
.btn-light { background: var(--admin-bg); color: var(--admin-muted); }
.btn-light:hover { border-color: var(--admin-primary); color: var(--admin-primary-dark); }
.btn-outline-danger { border-color: var(--admin-danger-border); background: transparent; color: var(--admin-danger-text); }
.btn-outline-danger:hover { background: var(--admin-danger-soft); }
.btn:disabled { cursor: not-allowed; opacity: 0.5; }

/* ── Thông báo ── */
.alert { margin: 0; padding: var(--admin-space-3) var(--admin-space-4); border-radius: var(--admin-radius-md); font-size: var(--admin-font-sm); }
.alert-success { border: 1px solid var(--admin-success-border); background: var(--admin-success-soft); color: var(--admin-success-text); }
.alert-danger { border: 1px solid var(--admin-danger-border); background: var(--admin-danger-soft); color: var(--admin-danger-text); }

/* ── Bảng ── */
.table-card { overflow: hidden; border: 1px solid var(--admin-border); border-radius: var(--admin-radius-lg); background: var(--admin-card); box-shadow: var(--admin-shadow-sm); }
.table-responsive { overflow-x: auto; }
.table { width: 100%; margin: 0; border-collapse: collapse; }
.table th {
  padding: var(--admin-space-3) var(--admin-space-5);
  border-bottom: 1px solid var(--admin-border);
  background: var(--admin-bg);
  color: var(--admin-muted);
  font-size: var(--admin-font-xs);
  font-weight: 700;
  letter-spacing: 0.05em;
  text-align: left;
  text-transform: uppercase;
  white-space: nowrap;
}
.table th.text-end { text-align: right; }
.table td {
  padding: var(--admin-space-4) var(--admin-space-5);
  border-bottom: 1px solid var(--admin-border-soft);
  color: var(--admin-text);
  font-size: var(--admin-font-sm);
  vertical-align: top;
}
.table tbody tr:last-child td { border-bottom: 0; }
.table tbody tr:hover td { background: var(--admin-bg); }
.table td strong { display: block; font-weight: 700; }
.table td small { display: block; margin-top: var(--admin-space-1); color: var(--admin-muted); font-size: var(--admin-font-xs); }
.comment-cell { min-width: 260px; max-width: 420px; }
.comment-text { margin: var(--admin-space-1) 0 0; white-space: pre-line; overflow-wrap: anywhere; }
.target-link { display: inline-flex; min-height: var(--admin-control-height); align-items: center; color: var(--admin-primary-dark); font-weight: 700; }
.table td small.reason { color: var(--admin-danger-text); }

.status-badge { display: inline-flex; padding: 3px 10px; border-radius: var(--admin-radius-pill); font-size: var(--admin-font-xs); font-weight: 700; white-space: nowrap; }
.status-pending { background: var(--admin-badge-pending-bg); color: var(--admin-badge-pending-text); }
.status-approved { background: var(--admin-badge-approved-bg); color: var(--admin-badge-approved-text); }
.status-rejected { background: var(--admin-badge-rejected-bg); color: var(--admin-badge-rejected-text); }

.row-actions { display: flex; justify-content: flex-end; gap: var(--admin-space-2); }

.pagination-bar { display: flex; align-items: center; justify-content: flex-end; gap: var(--admin-space-3); color: var(--admin-muted); font-size: var(--admin-font-sm); font-weight: 600; }

/* ── Hộp thoại từ chối (giống trang hồ sơ chủ thể) ── */
.modal-layer { position: fixed; z-index: 200; inset: 0; display: grid; padding: var(--admin-space-5); place-items: center; overflow-y: auto; background: var(--admin-scrim); }
.moderation-dialog { width: min(100%, 560px); max-height: calc(100vh - 40px); padding: var(--admin-space-6); overflow-y: auto; border-radius: var(--admin-radius-lg); background: var(--admin-card); box-shadow: var(--admin-shadow-modal); }
.moderation-dialog header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--admin-space-4); padding-bottom: var(--admin-space-4); border-bottom: 1px solid var(--admin-border-soft); }
.moderation-dialog header span { color: var(--admin-primary-dark); font-size: var(--admin-font-xs); font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; }
.moderation-dialog h2 { margin: var(--admin-space-1) 0 0; color: var(--admin-text); font-size: var(--admin-font-xl); }
.moderation-dialog header button { display: grid; width: var(--admin-control-height); height: var(--admin-control-height); flex: 0 0 auto; place-items: center; border: 0; border-radius: var(--admin-radius-sm); background: var(--admin-bg); color: var(--admin-muted); cursor: pointer; }
.moderation-dialog header button:hover { background: var(--admin-danger-soft); color: var(--admin-danger-text); }
.quoted-review { display: grid; gap: var(--admin-space-1); margin: var(--admin-space-4) 0; padding: var(--admin-space-4); border-radius: var(--admin-radius-md); background: var(--admin-bg); }
.quoted-review p { margin: 0; color: var(--admin-text); white-space: pre-line; overflow-wrap: anywhere; }
.quoted-review small { color: var(--admin-muted); }
.moderation-dialog form { display: grid; gap: var(--admin-space-2); }
.moderation-dialog form label span { color: var(--admin-text); font-size: var(--admin-font-sm); font-weight: 700; }
.moderation-dialog textarea.form-control { height: auto; padding: var(--admin-space-3); resize: vertical; }
.hint { margin: 0; color: var(--admin-muted); font-size: var(--admin-font-xs); }
.dialog-actions { display: flex; justify-content: flex-end; gap: var(--admin-space-2); margin-top: var(--admin-space-2); padding-top: var(--admin-space-4); border-top: 1px solid var(--admin-border-soft); }

@media (max-width: 991.98px) {
  .filter-bar { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 575.98px) {
  .page-heading { align-items: flex-start; flex-direction: column; }
  .filter-bar { grid-template-columns: 1fr; }
}
</style>
