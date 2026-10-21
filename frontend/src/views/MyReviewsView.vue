<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import ReviewForm from '@/components/reviews/ReviewForm.vue'
import ReviewStars from '@/components/reviews/ReviewStars.vue'
import StatusPanel from '@/components/ui/StatusPanel.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { deleteReview, listMyReviews, updateReview } from '@/services/reviews'
import type { MyReview, ReviewPayload } from '@/types/review'
import {
  formatReviewDate,
  REVIEW_STATUS_LABELS,
  reviewTargetLink,
  reviewTargetTypeLabel,
} from '@/utils/review'

const PAGE_SIZE = 10

const reviews = ref<MyReview[]>([])
const total = ref(0)
const page = ref(1)
const isLoading = ref(true)
const errorMessage = ref('')
const isLoadingMore = ref(false)
const loadMoreError = ref('')

const editingId = ref<number | null>(null)
const confirmingDeleteId = ref<number | null>(null)
const busyId = ref<number | null>(null)
const itemErrors = ref<Record<number, string>>({})
const notice = ref('')

const hasMore = computed(() => reviews.value.length < total.value)
const pendingCount = computed(() => reviews.value.filter((review) => review.status === 'pending').length)

let requestId = 0

async function loadReviews(): Promise<void> {
  const current = ++requestId
  isLoading.value = true
  errorMessage.value = ''
  loadMoreError.value = ''
  try {
    const response = await listMyReviews({ page: 1, page_size: PAGE_SIZE })
    if (current !== requestId) return
    reviews.value = response.items
    total.value = response.total
    page.value = 1
  } catch (error) {
    if (current !== requestId) return
    errorMessage.value = getApiErrorMessage(error, 'Chưa tải được đánh giá của bạn. Vui lòng thử lại.')
  } finally {
    if (current === requestId) isLoading.value = false
  }
}

async function loadMore(): Promise<void> {
  if (isLoadingMore.value) return
  const current = requestId
  isLoadingMore.value = true
  loadMoreError.value = ''
  try {
    const response = await listMyReviews({ page: page.value + 1, page_size: PAGE_SIZE })
    if (current !== requestId) return
    const known = new Set(reviews.value.map((review) => review.id))
    reviews.value = [...reviews.value, ...response.items.filter((review) => !known.has(review.id))]
    total.value = response.total
    page.value = response.page
  } catch (error) {
    if (current !== requestId) return
    loadMoreError.value = getApiErrorMessage(error, 'Chưa tải thêm được. Vui lòng thử lại.')
  } finally {
    isLoadingMore.value = false
  }
}

function setItemError(reviewId: number, message: string): void {
  itemErrors.value = { ...itemErrors.value, [reviewId]: message }
}

function startEdit(review: MyReview): void {
  notice.value = ''
  confirmingDeleteId.value = null
  setItemError(review.id, '')
  editingId.value = review.id
}

async function saveReview(review: MyReview, payload: ReviewPayload): Promise<void> {
  if (busyId.value !== null) return
  busyId.value = review.id
  setItemError(review.id, '')
  try {
    const updated = await updateReview(review.id, payload)
    reviews.value = reviews.value.map((item) => (item.id === updated.id ? updated : item))
    editingId.value = null
    notice.value = `Đã lưu đánh giá cho "${updated.target.name}". Đánh giá sẽ hiển thị lại sau khi được duyệt.`
  } catch (error) {
    setItemError(review.id, getApiErrorMessage(error, 'Chưa lưu được đánh giá. Vui lòng thử lại.'))
  } finally {
    busyId.value = null
  }
}

async function removeReview(review: MyReview): Promise<void> {
  if (busyId.value !== null) return
  busyId.value = review.id
  setItemError(review.id, '')
  try {
    await deleteReview(review.id)
    reviews.value = reviews.value.filter((item) => item.id !== review.id)
    total.value = Math.max(0, total.value - 1)
    confirmingDeleteId.value = null
    notice.value = `Đã xóa đánh giá cho "${review.target.name}".`
  } catch (error) {
    setItemError(review.id, getApiErrorMessage(error, 'Chưa xóa được đánh giá. Vui lòng thử lại.'))
  } finally {
    busyId.value = null
  }
}

onMounted(loadReviews)
onUnmounted(() => {
  requestId++
})
</script>

<template>
  <main class="my-reviews-page">
    <div class="container py-4 py-lg-5">
      <nav class="breadcrumb-nav" aria-label="Đường dẫn">
        <RouterLink to="/tai-khoan">Tài khoản</RouterLink>
        <span aria-hidden="true">/</span>
        <span aria-current="page">Đánh giá của tôi</span>
      </nav>

      <header class="page-head">
        <p class="ocop-eyebrow">Tài khoản cá nhân</p>
        <h1 class="ocop-section-title">Đánh giá của tôi</h1>
        <p class="ocop-section-copy">
          Xem lại, sửa hoặc xóa các đánh giá bạn đã viết. Đánh giá mới hoặc vừa sửa sẽ hiển thị sau khi được duyệt.
        </p>
      </header>

      <p v-if="notice" class="notice" role="status">{{ notice }}</p>

      <StatusPanel v-if="isLoading" kind="loading" :rows="3" message="Đang tải đánh giá của bạn…" />
      <StatusPanel v-else-if="errorMessage" kind="error" :message="errorMessage" @retry="loadReviews" />
      <StatusPanel
        v-else-if="reviews.length === 0"
        kind="empty"
        title="Bạn chưa viết đánh giá nào"
        message="Hãy chia sẻ cảm nhận về sản phẩm OCOP hoặc điểm du lịch bạn đã ghé thăm."
      >
        <div class="empty-actions">
          <RouterLink class="ocop-btn-main" to="/san-pham">Xem sản phẩm OCOP</RouterLink>
          <RouterLink class="ocop-btn-ghost" to="/diem-du-lich">Xem điểm du lịch</RouterLink>
        </div>
      </StatusPanel>

      <template v-else>
        <p class="list-meta">
          {{ total }} đánh giá<template v-if="pendingCount"> · {{ pendingCount }} đang chờ duyệt</template>
        </p>
        <ul class="my-review-list">
          <li v-for="review in reviews" :key="review.id" class="my-review-card" :data-test="`review-${review.id}`">
            <header class="card-head">
              <div class="card-target">
                <span class="target-type">{{ reviewTargetTypeLabel(review.target) }}</span>
                <RouterLink class="target-link" :to="reviewTargetLink(review.target)">{{ review.target.name }}</RouterLink>
              </div>
              <span class="status-pill" :class="`is-${review.status}`">{{ REVIEW_STATUS_LABELS[review.status] }}</span>
            </header>

            <template v-if="editingId === review.id">
              <ReviewForm
                :id-prefix="`my-review-${review.id}`"
                :initial-rating="review.rating"
                :initial-comment="review.comment"
                :submitting="busyId === review.id"
                submit-label="Lưu thay đổi"
                :error-message="itemErrors[review.id] ?? ''"
                cancelable
                @submit="(payload) => saveReview(review, payload)"
                @cancel="editingId = null"
              />
            </template>

            <template v-else>
              <div class="card-rating">
                <ReviewStars :rating="review.rating" />
                <time :datetime="review.updated_at">Cập nhật {{ formatReviewDate(review.updated_at) }}</time>
              </div>
              <p class="review-comment">{{ review.comment }}</p>
              <p v-if="review.status === 'rejected'" class="rejection" data-test="rejection-reason">
                <strong>Bị từ chối:</strong> {{ review.rejection_reason }}
                <span>Bạn có thể sửa lại nội dung để gửi duyệt lần nữa.</span>
              </p>
              <p v-if="itemErrors[review.id]" class="form-alert" role="alert">{{ itemErrors[review.id] }}</p>

              <div v-if="confirmingDeleteId === review.id" class="card-actions" role="group" aria-label="Xác nhận xóa đánh giá">
                <span class="confirm-text">Xóa đánh giá này? Bạn không thể khôi phục.</span>
                <button class="ocop-btn-ghost" type="button" :disabled="busyId === review.id" @click="confirmingDeleteId = null">
                  Giữ lại
                </button>
                <button class="btn-danger-solid" type="button" :disabled="busyId === review.id" data-test="confirm-delete" @click="removeReview(review)">
                  {{ busyId === review.id ? 'Đang xóa…' : 'Xóa đánh giá' }}
                </button>
              </div>
              <div v-else class="card-actions">
                <button class="ocop-btn-ghost" type="button" data-test="edit" @click="startEdit(review)">
                  <i class="bi bi-pencil" aria-hidden="true" /> Sửa<span class="visually-hidden"> đánh giá {{ review.target.name }}</span>
                </button>
                <button class="ocop-btn-ghost is-danger" type="button" data-test="delete" @click="confirmingDeleteId = review.id">
                  <i class="bi bi-trash" aria-hidden="true" /> Xóa<span class="visually-hidden"> đánh giá {{ review.target.name }}</span>
                </button>
              </div>
            </template>
          </li>
        </ul>

        <p v-if="loadMoreError" class="form-alert" role="alert">{{ loadMoreError }}</p>
        <div v-if="hasMore || loadMoreError" class="load-more">
          <button class="ocop-btn-ghost" type="button" :disabled="isLoadingMore" data-test="load-more" @click="loadMore">
            {{ isLoadingMore ? 'Đang tải…' : loadMoreError ? 'Thử lại' : 'Xem thêm' }}
          </button>
        </div>
      </template>
    </div>
  </main>
</template>

<style scoped>
.my-reviews-page {
  min-height: calc(100vh - var(--ocop-space-16));
  background: var(--ocop-surface);
}

.container {
  display: grid;
  gap: var(--ocop-space-4);
  max-width: calc(var(--ocop-content) * 0.7);
}

.breadcrumb-nav {
  display: flex;
  flex-wrap: wrap;
  gap: var(--ocop-space-2);
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-small);
}

.breadcrumb-nav a {
  color: var(--ocop-primary-700);
}

.page-head {
  display: grid;
  gap: var(--ocop-space-1);
}

.page-head h1 {
  font-size: var(--ocop-font-size-title-lg);
}

.notice {
  margin: 0;
  padding: var(--ocop-space-3) var(--ocop-space-4);
  border: 1px solid var(--ocop-success);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-success-soft);
  color: var(--ocop-success);
  font-weight: 600;
}

.empty-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--ocop-space-2);
  margin-top: var(--ocop-space-3);
}

.list-meta {
  margin: 0;
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-body);
}

.my-review-list {
  display: grid;
  gap: var(--ocop-space-3);
  margin: 0;
  padding: 0;
  list-style: none;
}

.my-review-card {
  display: grid;
  gap: var(--ocop-space-3);
  padding: var(--ocop-space-5);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
}

.card-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--ocop-space-2);
}

.card-target {
  display: grid;
  min-width: 0;
}

.target-type {
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.target-link {
  display: inline-flex;
  min-height: var(--ocop-control-md);
  align-items: center;
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-title-sm);
  font-weight: 750;
  overflow-wrap: anywhere;
}

.status-pill {
  display: inline-flex;
  padding: var(--ocop-space-1) var(--ocop-space-3);
  border-radius: var(--ocop-radius-pill);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
  white-space: nowrap;
}

.status-pill.is-pending {
  background: var(--ocop-warning-soft);
  color: var(--ocop-warning-strong);
}

.status-pill.is-approved {
  background: var(--ocop-success-soft);
  color: var(--ocop-success);
}

.status-pill.is-rejected {
  background: var(--ocop-danger-soft);
  color: var(--ocop-danger-strong);
}

.card-rating {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--ocop-space-3);
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-small);
}

.review-comment {
  margin: 0;
  color: var(--ocop-text-primary);
  white-space: pre-line;
  overflow-wrap: anywhere;
}

.rejection {
  display: grid;
  gap: var(--ocop-space-1);
  margin: 0;
  padding: var(--ocop-space-3);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-danger-soft);
  color: var(--ocop-danger-strong);
}

.rejection span {
  color: var(--ocop-text-primary);
  font-size: var(--ocop-font-size-small);
}

.form-alert {
  margin: 0;
  padding: var(--ocop-space-3) var(--ocop-space-4);
  border: 1px solid var(--ocop-danger-border);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-danger-soft);
  color: var(--ocop-danger-strong);
}

.card-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: var(--ocop-space-2);
}

.confirm-text {
  flex: 1 1 14rem;
  font-weight: 600;
}

.ocop-btn-ghost.is-danger {
  color: var(--ocop-danger-strong);
}

.ocop-btn-ghost.is-danger:hover {
  border-color: var(--ocop-danger-border);
  background: var(--ocop-danger-soft);
}

.btn-danger-solid {
  display: inline-flex;
  min-height: var(--ocop-control-md);
  align-items: center;
  padding: 0 var(--ocop-space-5);
  border: 1px solid var(--ocop-danger-strong);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-danger-strong);
  color: var(--ocop-white);
  font-weight: 700;
}

.my-reviews-page button:focus-visible,
.my-reviews-page a:focus-visible {
  outline: 3px solid var(--ocop-primary-500);
  outline-offset: 2px;
}

.my-reviews-page button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.load-more {
  display: flex;
  justify-content: center;
}
</style>
