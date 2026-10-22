<script setup lang="ts">
import axios from 'axios'
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import ReviewForm from '@/components/reviews/ReviewForm.vue'
import ReviewStars from '@/components/reviews/ReviewStars.vue'
import StatusPanel from '@/components/ui/StatusPanel.vue'
import { getApiErrorMessage } from '@/services/api-error'
import {
  createReview,
  deleteReview,
  getPublicReviews,
  listMyReviews,
  updateReview,
} from '@/services/reviews'
import { getMySubjectApplication } from '@/services/subjects'
import { authStore } from '@/stores/auth'
import type { MyReview, PublicReview, ReviewPayload, ReviewSummary, ReviewTargetType } from '@/types/review'
import { formatAverage, formatReviewDate, REVIEW_STATUS_LABELS } from '@/utils/review'

/**
 * Khối đánh giá cuối trang chi tiết sản phẩm / điểm du lịch: tóm tắt sao, danh sách đánh giá đã duyệt
 * và form viết đánh giá cho người đã đăng nhập.
 */
const props = withDefaults(
  defineProps<{
    targetType: ReviewTargetType
    targetId: number
    /** Chủ thể sở hữu sản phẩm/điểm: chủ thể đó không tự đánh giá (backend vẫn chặn). */
    ownerSubjectId?: number | null
  }>(),
  { ownerSubjectId: null },
)

const PAGE_SIZE = 5

const route = useRoute()

const reviews = ref<PublicReview[]>([])
const summary = ref<ReviewSummary | null>(null)
const total = ref(0)
const page = ref(1)
const isLoading = ref(true)
const loadError = ref('')
const isLoadingMore = ref(false)
const loadMoreError = ref('')

const myReview = ref<MyReview | null>(null)
const mySubjectId = ref<number | null>(null)
const isEditing = ref(false)
const isSubmitting = ref(false)
const formError = ref('')
const notice = ref('')
const isConfirmingDelete = ref(false)
const isDeleting = ref(false)
const noticeRef = ref<HTMLElement | null>(null)
const deleteAlertRef = ref<HTMLElement | null>(null)

const headingId = computed(() => `review-heading-${props.targetType}-${props.targetId}`)
const user = computed(() => authStore.currentUser.value)
const isAuthenticated = computed(() => authStore.isAuthenticated.value)
const isAdmin = computed(() => user.value?.role === 'admin')
const isOwner = computed(
  () => props.ownerSubjectId !== null && mySubjectId.value !== null && mySubjectId.value === props.ownerSubjectId,
)
const canWrite = computed(() => isAuthenticated.value && !isAdmin.value && !isOwner.value)
const loginLink = computed(() => ({ path: '/dang-nhap', query: { redirect: route.fullPath } }))
const targetNoun = computed(() => (props.targetType === 'product' ? 'sản phẩm' : 'điểm du lịch'))
const hasMore = computed(() => reviews.value.length < total.value)
const distribution = computed(() =>
  [5, 4, 3, 2, 1].map((star) => {
    const count = summary.value?.distribution[String(star)] ?? 0
    const share = summary.value?.count ? Math.round((count / summary.value.count) * 100) : 0
    return { star, count, share }
  }),
)

// Bỏ kết quả cũ khi người dùng chuyển sang sản phẩm/điểm khác trong lúc đang tải.
let listRequestId = 0
let mineRequestId = 0

async function loadReviews(): Promise<void> {
  const requestId = ++listRequestId
  isLoading.value = true
  loadError.value = ''
  loadMoreError.value = ''
  try {
    const response = await getPublicReviews(props.targetType, props.targetId, { page: 1, page_size: PAGE_SIZE })
    if (requestId !== listRequestId) return
    reviews.value = response.items
    summary.value = response.summary
    total.value = response.total
    page.value = 1
  } catch (error) {
    if (requestId !== listRequestId) return
    loadError.value = getApiErrorMessage(error, 'Chưa tải được đánh giá. Vui lòng thử lại.')
  } finally {
    if (requestId === listRequestId) isLoading.value = false
  }
}

async function loadMore(): Promise<void> {
  if (isLoadingMore.value) return
  const requestId = listRequestId
  isLoadingMore.value = true
  loadMoreError.value = ''
  try {
    const response = await getPublicReviews(props.targetType, props.targetId, {
      page: page.value + 1,
      page_size: PAGE_SIZE,
    })
    if (requestId !== listRequestId) return
    const known = new Set(reviews.value.map((review) => review.id))
    reviews.value = [...reviews.value, ...response.items.filter((review) => !known.has(review.id))]
    total.value = response.total
    summary.value = response.summary
    page.value = response.page
  } catch (error) {
    if (requestId !== listRequestId) return
    loadMoreError.value = getApiErrorMessage(error, 'Chưa tải thêm được đánh giá. Vui lòng thử lại.')
  } finally {
    isLoadingMore.value = false
  }
}

async function loadMine(): Promise<void> {
  const requestId = ++mineRequestId
  myReview.value = null
  mySubjectId.value = null
  if (!isAuthenticated.value || isAdmin.value) return
  try {
    const filter = props.targetType === 'product' ? { product_id: props.targetId } : { location_id: props.targetId }
    const [mine, subjectId] = await Promise.all([
      listMyReviews({ ...filter, page_size: 1 }),
      user.value?.role === 'subject' && props.ownerSubjectId !== null
        ? getMySubjectApplication().then((subject) => subject.id).catch(() => null)
        : Promise.resolve(null),
    ])
    if (requestId !== mineRequestId) return
    myReview.value = mine.items[0] ?? null
    mySubjectId.value = subjectId
  } catch {
    // Không lấy được đánh giá của tôi thì vẫn cho viết; backend trả 409 nếu đã có.
    if (requestId === mineRequestId) myReview.value = null
  }
}

function resetForm(): void {
  isEditing.value = false
  isConfirmingDelete.value = false
  formError.value = ''
  notice.value = ''
}

watch(
  () => [props.targetType, props.targetId] as const,
  () => {
    resetForm()
    reviews.value = []
    summary.value = null
    total.value = 0
    void loadReviews()
    void loadMine()
  },
  { immediate: true },
)

watch(
  () => user.value?.id,
  (next, previous) => {
    if (next !== previous) void loadMine()
  },
)

onUnmounted(() => {
  listRequestId++
  mineRequestId++
})

// Sau khi gửi, sửa hoặc xóa thành công form biến mất: đưa focus tới thông báo để không rơi về BODY.
function focusNotice(): void {
  void nextTick(() => noticeRef.value?.focus())
}

async function submitReview(payload: ReviewPayload): Promise<void> {
  if (isSubmitting.value) return
  isSubmitting.value = true
  formError.value = ''
  notice.value = ''
  const wasApproved = myReview.value?.status === 'approved'
  try {
    if (myReview.value) {
      myReview.value = await updateReview(myReview.value.id, payload)
      notice.value = 'Đã lưu thay đổi. Đánh giá sẽ hiển thị lại sau khi được duyệt.'
    } else {
      myReview.value = await createReview(props.targetType, props.targetId, payload)
      notice.value = 'Cảm ơn bạn! Đánh giá sẽ hiển thị sau khi được duyệt.'
    }
    isEditing.value = false
    focusNotice()
    if (wasApproved) void loadReviews()
  } catch (error) {
    formError.value = getApiErrorMessage(error, 'Chưa gửi được đánh giá. Vui lòng thử lại.')
    if (axios.isAxiosError(error) && error.response?.status === 409) {
      // Đã đánh giá từ trước (ví dụ ở thẻ khác): hiện lại đánh giá cũ để người dùng sửa.
      await loadMine()
    }
  } finally {
    isSubmitting.value = false
  }
}

async function confirmDelete(): Promise<void> {
  if (!myReview.value || isDeleting.value) return
  isDeleting.value = true
  formError.value = ''
  const wasApproved = myReview.value.status === 'approved'
  try {
    await deleteReview(myReview.value.id)
    myReview.value = null
    isConfirmingDelete.value = false
    notice.value = 'Đã xóa đánh giá của bạn.'
    focusNotice()
    if (wasApproved) void loadReviews()
  } catch (error) {
    formError.value = getApiErrorMessage(error, 'Chưa xóa được đánh giá. Vui lòng thử lại.')
    void nextTick(() => deleteAlertRef.value?.focus())
  } finally {
    isDeleting.value = false
  }
}

function startEdit(): void {
  notice.value = ''
  formError.value = ''
  isConfirmingDelete.value = false
  isEditing.value = true
}
</script>

<template>
  <section class="review-section" :aria-labelledby="headingId">
    <div class="ocop-section-head">
      <div>
        <p class="ocop-eyebrow">Cảm nhận của người dùng</p>
        <h2 :id="headingId" class="ocop-section-title">Đánh giá &amp; nhận xét</h2>
      </div>
    </div>

    <StatusPanel v-if="isLoading" kind="loading" :rows="2" message="Đang tải đánh giá…" />
    <StatusPanel v-else-if="loadError" kind="error" :message="loadError" @retry="loadReviews" />

    <div v-else class="review-layout">
      <aside class="review-summary" aria-label="Tóm tắt đánh giá">
        <template v-if="summary && summary.count > 0">
          <p class="summary-score">
            <strong>{{ formatAverage(summary.average) }}</strong>
            <span>/ 5</span>
          </p>
          <ReviewStars :rating="summary.average" size="lg" />
          <p class="summary-count">{{ summary.count }} đánh giá đã duyệt</p>
          <ul class="distribution">
            <li v-for="row in distribution" :key="row.star">
              <span class="distribution-label">{{ row.star }} sao</span>
              <span class="distribution-bar" aria-hidden="true">
                <span class="distribution-fill" :style="{ width: `${row.share}%` }" />
              </span>
              <span class="distribution-count">{{ row.count }}<span class="visually-hidden"> đánh giá</span></span>
            </li>
          </ul>
        </template>
        <p v-else class="summary-empty">Chưa có điểm đánh giá cho {{ targetNoun }} này.</p>
      </aside>

      <div class="review-main">
        <div class="write-area" data-test="write-area">
          <p v-if="notice" ref="noticeRef" class="notice" role="status" tabindex="-1">{{ notice }}</p>

          <div v-if="!isAuthenticated" class="write-prompt">
            <p>Bạn đã dùng {{ targetNoun }} này? Đăng nhập để chia sẻ cảm nhận với mọi người.</p>
            <RouterLink class="ocop-btn-main" data-test="login-to-review" :to="loginLink">
              Đăng nhập để đánh giá
            </RouterLink>
          </div>

          <p v-else-if="isAdmin" class="write-note">
            Tài khoản quản trị không viết đánh giá. Bạn có thể duyệt đánh giá tại
            <RouterLink to="/quan-tri/danh-gia">trang quản trị</RouterLink>.
          </p>

          <p v-else-if="isOwner" class="write-note" data-test="owner-note">
            Đây là {{ targetNoun }} của đơn vị bạn nên bạn không tự đánh giá được. Đánh giá do khách hàng gửi
            sẽ hiển thị ở đây sau khi được duyệt.
          </p>

          <article v-else-if="myReview && !isEditing" class="my-review" data-test="my-review">
            <header>
              <h3>Đánh giá của bạn</h3>
              <span class="status-pill" :class="`is-${myReview.status}`">
                {{ REVIEW_STATUS_LABELS[myReview.status] }}
              </span>
            </header>
            <ReviewStars :rating="myReview.rating" />
            <p class="review-comment">{{ myReview.comment }}</p>
            <p v-if="myReview.status === 'rejected'" class="rejection" data-test="rejection-reason">
              <strong>Bị từ chối:</strong> {{ myReview.rejection_reason }}
            </p>
            <p v-else-if="myReview.status === 'pending'" class="write-hint">
              Đánh giá sẽ hiển thị công khai sau khi ban quản trị duyệt.
            </p>
            <p v-if="formError" ref="deleteAlertRef" class="form-alert" role="alert" tabindex="-1">{{ formError }}</p>
            <div v-if="isConfirmingDelete" class="confirm-row" role="group" aria-label="Xác nhận xóa đánh giá">
              <span>Xóa đánh giá này? Bạn không thể khôi phục.</span>
              <button class="ocop-btn-ghost" type="button" :disabled="isDeleting" @click="isConfirmingDelete = false">
                Giữ lại
              </button>
              <button class="btn-danger-solid" type="button" :disabled="isDeleting" data-test="confirm-delete" @click="confirmDelete">
                {{ isDeleting ? 'Đang xóa…' : 'Xóa đánh giá' }}
              </button>
            </div>
            <div v-else class="my-review-actions">
              <button class="ocop-btn-ghost" type="button" data-test="edit-review" @click="startEdit">
                <i class="bi bi-pencil" aria-hidden="true" /> Sửa
              </button>
              <button class="ocop-btn-ghost is-danger" type="button" data-test="delete-review" @click="isConfirmingDelete = true">
                <i class="bi bi-trash" aria-hidden="true" /> Xóa
              </button>
            </div>
          </article>

          <div v-else-if="canWrite" class="write-form">
            <h3>{{ myReview ? 'Sửa đánh giá của bạn' : 'Viết đánh giá' }}</h3>
            <p v-if="myReview" class="write-hint">Sau khi sửa, đánh giá sẽ được duyệt lại trước khi hiển thị.</p>
            <ReviewForm
              :id-prefix="`review-${targetType}-${targetId}`"
              :initial-rating="myReview?.rating ?? null"
              :initial-comment="myReview?.comment ?? ''"
              :submitting="isSubmitting"
              :submit-label="myReview ? 'Lưu thay đổi' : 'Gửi đánh giá'"
              :error-message="formError"
              :cancelable="Boolean(myReview)"
              @submit="submitReview"
              @cancel="isEditing = false"
            />
          </div>
        </div>

        <StatusPanel
          v-if="reviews.length === 0"
          kind="empty"
          title="Chưa có đánh giá nào"
          :message="`Hãy là người đầu tiên chia sẻ cảm nhận về ${targetNoun} này.`"
        />
        <template v-else>
          <ol class="review-list" aria-label="Danh sách đánh giá">
            <li v-for="review in reviews" :key="review.id" class="review-item">
              <header>
                <span class="review-avatar" aria-hidden="true">{{ review.author_name.trim().charAt(0).toUpperCase() }}</span>
                <span class="review-author">
                  <strong>{{ review.author_name }}</strong>
                  <time :datetime="review.created_at">{{ formatReviewDate(review.created_at) }}</time>
                </span>
                <ReviewStars :rating="review.rating" size="sm" />
              </header>
              <p class="review-comment">{{ review.comment }}</p>
            </li>
          </ol>
          <p v-if="loadMoreError" class="form-alert" role="alert">{{ loadMoreError }}</p>
          <div v-if="hasMore || loadMoreError" class="load-more">
            <button class="ocop-btn-ghost" type="button" :disabled="isLoadingMore" data-test="load-more" @click="loadMore">
              {{ isLoadingMore ? 'Đang tải…' : loadMoreError ? 'Thử lại' : `Xem thêm đánh giá (${total - reviews.length})` }}
            </button>
          </div>
        </template>
      </div>
    </div>
  </section>
</template>

<style scoped>
.review-section {
  display: grid;
  gap: var(--ocop-space-5);
  margin-top: var(--ocop-space-12);
  padding-top: var(--ocop-space-8);
  border-top: 1px solid var(--ocop-border);
}

.review-layout {
  display: grid;
  gap: var(--ocop-space-6);
}

.review-summary,
.write-area > *,
.review-item {
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
}

.review-summary {
  display: grid;
  align-content: start;
  justify-items: start;
  gap: var(--ocop-space-2);
  padding: var(--ocop-space-5);
}

.summary-score {
  display: flex;
  align-items: baseline;
  gap: var(--ocop-space-1);
  margin: 0;
  color: var(--ocop-text-primary);
}

.summary-score strong {
  font-size: var(--ocop-font-size-title-lg);
  font-weight: 800;
  line-height: 1;
}

.summary-score span,
.summary-count,
.summary-empty {
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-body);
}

.summary-count,
.summary-empty {
  margin: 0;
}

.distribution {
  display: grid;
  width: 100%;
  gap: var(--ocop-space-2);
  margin: var(--ocop-space-2) 0 0;
  padding: 0;
  list-style: none;
}

.distribution li {
  display: grid;
  grid-template-columns: var(--ocop-space-12) minmax(0, 1fr) var(--ocop-space-8);
  align-items: center;
  gap: var(--ocop-space-2);
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-small);
}

.distribution-bar {
  height: var(--ocop-space-2);
  overflow: hidden;
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-mist-100);
}

.distribution-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--ocop-daquy-500);
}

.distribution-count {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.review-main {
  display: grid;
  align-content: start;
  gap: var(--ocop-space-4);
  min-width: 0;
}

.write-area {
  display: grid;
  gap: var(--ocop-space-3);
}

.write-area > .notice {
  margin: 0;
  padding: var(--ocop-space-3) var(--ocop-space-4);
  border-color: var(--ocop-success);
  background: var(--ocop-success-soft);
  color: var(--ocop-success);
  font-weight: 600;
}

.write-prompt,
.write-note,
.write-form,
.my-review {
  padding: var(--ocop-space-5);
}

.write-prompt {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--ocop-space-3);
}

.write-prompt p,
.write-note {
  margin: 0;
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-body);
}

.write-note {
  background: var(--ocop-surface-muted);
}

.write-note a {
  color: var(--ocop-primary-700);
  font-weight: 650;
}

.write-form h3,
.my-review h3 {
  margin: 0 0 var(--ocop-space-3);
  color: var(--ocop-text-primary);
  font-size: var(--ocop-font-size-title-sm);
  font-weight: 750;
}

.write-hint {
  margin: 0 0 var(--ocop-space-3);
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-small);
}

.my-review {
  display: grid;
  gap: var(--ocop-space-2);
}

.my-review header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--ocop-space-2);
}

.my-review h3 {
  margin: 0;
}

.status-pill {
  display: inline-flex;
  padding: var(--ocop-space-1) var(--ocop-space-3);
  border-radius: var(--ocop-radius-pill);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
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

.rejection {
  margin: 0;
  padding: var(--ocop-space-3);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-danger-soft);
  color: var(--ocop-danger-strong);
  font-size: var(--ocop-font-size-body);
}

.form-alert {
  margin: 0;
  padding: var(--ocop-space-3) var(--ocop-space-4);
  border: 1px solid var(--ocop-danger-border);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-danger-soft);
  color: var(--ocop-danger-strong);
  font-size: var(--ocop-font-size-body);
}

.my-review-actions,
.confirm-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--ocop-space-2);
  margin-top: var(--ocop-space-2);
}

.confirm-row span {
  flex: 1 1 14rem;
  color: var(--ocop-text-primary);
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
  font-size: var(--ocop-font-size-body);
  font-weight: 700;
}

.review-section button:focus-visible,
.review-section a:focus-visible {
  outline: 3px solid var(--ocop-primary-500);
  outline-offset: 2px;
}

.review-section button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.review-list {
  display: grid;
  gap: var(--ocop-space-3);
  margin: 0;
  padding: 0;
  list-style: none;
}

.review-item {
  padding: var(--ocop-space-4) var(--ocop-space-5);
}

.review-item header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--ocop-space-3);
}

.review-avatar {
  display: grid;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  background: var(--ocop-mist-100);
  color: var(--ocop-mist-800);
  font-weight: 750;
}

.review-author {
  display: grid;
  flex: 1 1 auto;
  min-width: 0;
}

.review-author strong {
  overflow-wrap: anywhere;
  color: var(--ocop-text-primary);
}

.review-author time {
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-small);
}

.review-comment {
  margin: var(--ocop-space-3) 0 0;
  color: var(--ocop-text-primary);
  font-size: var(--ocop-font-size-body);
  white-space: pre-line;
  overflow-wrap: anywhere;
}

.my-review .review-comment {
  margin: 0;
}

.load-more {
  display: flex;
  justify-content: center;
}

@media (min-width: 992px) {
  .review-layout {
    grid-template-columns: minmax(240px, 300px) minmax(0, 1fr);
    align-items: start;
  }

  .review-summary {
    position: sticky;
    top: calc(var(--ocop-space-16) + var(--ocop-space-4));
  }
}
</style>
