<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

import type { ReviewPayload } from '@/types/review'
import {
  RATING_LABELS,
  REVIEW_COMMENT_MAX,
  REVIEW_COMMENT_MIN,
  validateReviewComment,
} from '@/utils/review'

/** Form viết hoặc sửa đánh giá: chọn sao (nhóm radio có nhãn) và nhận xét có đếm ký tự. */
const props = withDefaults(
  defineProps<{
    idPrefix: string
    initialRating?: number | null
    initialComment?: string
    submitting?: boolean
    submitLabel?: string
    errorMessage?: string
    cancelable?: boolean
  }>(),
  {
    initialRating: null,
    initialComment: '',
    submitting: false,
    submitLabel: 'Gửi đánh giá',
    errorMessage: '',
    cancelable: false,
  },
)

const emit = defineEmits<{ submit: [payload: ReviewPayload]; cancel: [] }>()

const rating = ref<number | null>(props.initialRating)
const comment = ref(props.initialComment)
const attempted = ref(false)
const formRef = ref<HTMLFormElement | null>(null)
const alertRef = ref<HTMLElement | null>(null)
const commentRef = ref<HTMLTextAreaElement | null>(null)

watch(
  () => [props.initialRating, props.initialComment] as const,
  ([nextRating, nextComment]) => {
    rating.value = nextRating
    comment.value = nextComment
    attempted.value = false
  },
)

const commentLength = computed(() => comment.value.trim().length)
const ratingError = computed(() => (attempted.value && !rating.value ? 'Vui lòng chọn số sao.' : ''))
const commentError = computed(() => (attempted.value ? validateReviewComment(comment.value) : ''))
const ratingHint = computed(() =>
  rating.value ? `Bạn chọn ${rating.value} sao: ${RATING_LABELS[rating.value]}.` : 'Chọn từ 1 đến 5 sao.',
)

const ids = computed(() => ({
  legend: `${props.idPrefix}-rating-legend`,
  ratingHint: `${props.idPrefix}-rating-hint`,
  comment: `${props.idPrefix}-comment`,
  commentHint: `${props.idPrefix}-comment-hint`,
  commentError: `${props.idPrefix}-comment-error`,
}))

// Trợ năng: lỗi nhập thì đưa focus tới ô lỗi đầu tiên (nhóm sao rồi tới nhận xét); lỗi từ máy chủ thì
// tới khối thông báo lỗi đầu form, để người dùng bàn phím và trình đọc màn hình không phải tự tìm.
function focusFirstInvalid(): void {
  if (!rating.value) formRef.value?.querySelector<HTMLInputElement>('input[type="radio"]')?.focus()
  else commentRef.value?.focus()
}

function submit(): void {
  attempted.value = true
  if (!rating.value || validateReviewComment(comment.value)) {
    void nextTick(focusFirstInvalid)
    return
  }
  emit('submit', { rating: rating.value, comment: comment.value.trim() })
}

watch(
  () => props.errorMessage,
  (message) => {
    if (message) void nextTick(() => alertRef.value?.focus())
  },
)
</script>

<template>
  <form ref="formRef" class="review-form" novalidate @submit.prevent="submit">
    <p v-if="errorMessage" ref="alertRef" class="form-alert" role="alert" tabindex="-1">{{ errorMessage }}</p>

    <fieldset class="rating-field" :aria-describedby="ids.ratingHint">
      <legend :id="ids.legend">Bạn chấm mấy sao? <span class="required-mark" aria-hidden="true">*</span></legend>
      <div class="rating-options">
        <label v-for="star in 5" :key="star" class="rating-option" :class="{ 'is-active': rating !== null && star <= rating }">
          <input
            v-model="rating"
            type="radio"
            :name="`${idPrefix}-rating`"
            :value="star"
            :aria-invalid="ratingError ? 'true' : undefined"
          />
          <i class="bi" :class="rating !== null && star <= rating ? 'bi-star-fill' : 'bi-star'" aria-hidden="true" />
          <span class="rating-number">{{ star }}</span>
          <span class="visually-hidden">sao, {{ RATING_LABELS[star] }}</span>
        </label>
      </div>
      <p :id="ids.ratingHint" class="field-hint">{{ ratingHint }}</p>
      <p v-if="ratingError" class="field-error" role="alert">{{ ratingError }}</p>
    </fieldset>

    <div class="comment-field">
      <label :for="ids.comment">Nhận xét của bạn <span class="required-mark" aria-hidden="true">*</span></label>
      <textarea
        :id="ids.comment"
        ref="commentRef"
        v-model="comment"
        class="form-control"
        rows="4"
        :maxlength="REVIEW_COMMENT_MAX"
        required
        :aria-invalid="commentError ? 'true' : undefined"
        :aria-describedby="commentError ? `${ids.commentHint} ${ids.commentError}` : ids.commentHint"
        placeholder="Chia sẻ trải nghiệm thật của bạn: chất lượng, hương vị, cách phục vụ..."
      />
      <p :id="ids.commentHint" class="field-hint comment-meta">
        <span>Từ {{ REVIEW_COMMENT_MIN }} đến {{ REVIEW_COMMENT_MAX }} ký tự.</span>
        <span class="char-count" :class="{ 'is-short': commentLength > 0 && commentLength < REVIEW_COMMENT_MIN }">
          {{ commentLength }}/{{ REVIEW_COMMENT_MAX }} ký tự
        </span>
      </p>
      <p v-if="commentError" :id="ids.commentError" class="field-error" role="alert">{{ commentError }}</p>
    </div>

    <div class="form-actions">
      <button v-if="cancelable" class="ocop-btn-ghost" type="button" :disabled="submitting" @click="emit('cancel')">
        Hủy
      </button>
      <button class="ocop-btn-main" type="submit" :disabled="submitting">
        {{ submitting ? 'Đang gửi…' : submitLabel }}
      </button>
    </div>
  </form>
</template>

<style scoped>
.review-form {
  display: grid;
  gap: var(--ocop-space-4);
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

.rating-field {
  margin: 0;
  padding: 0;
  border: 0;
  min-width: 0;
}

.rating-field legend,
.comment-field label {
  display: block;
  margin-bottom: var(--ocop-space-2);
  color: var(--ocop-text-primary);
  font-size: var(--ocop-font-size-body);
  font-weight: 700;
}

.required-mark {
  color: var(--ocop-danger-strong);
}

.rating-options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--ocop-space-2);
}

.rating-option {
  position: relative;
  display: inline-flex;
  min-width: var(--ocop-control-md);
  min-height: var(--ocop-control-md);
  align-items: center;
  justify-content: center;
  gap: var(--ocop-space-1);
  padding: 0 var(--ocop-space-3);
  border: 1px solid var(--ocop-border-strong);
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-card);
  color: var(--ocop-text-muted);
  font-weight: 700;
  cursor: pointer;
  transition: border-color var(--ocop-transition), background var(--ocop-transition);
}

.rating-option input {
  position: absolute;
  inset: 0;
  margin: 0;
  opacity: 0;
  cursor: pointer;
}

.rating-option:hover {
  border-color: var(--ocop-daquy-600);
}

.rating-option.is-active {
  border-color: var(--ocop-daquy-500);
  background: var(--ocop-daquy-50);
  color: var(--ocop-mist-950);
}

.rating-option.is-active .bi {
  color: var(--ocop-daquy-700);
}

.rating-option:has(input:focus-visible) {
  outline: 3px solid var(--ocop-primary-500);
  outline-offset: 2px;
}

.field-hint {
  margin: var(--ocop-space-2) 0 0;
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-small);
}

.comment-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--ocop-space-2);
}

.char-count {
  font-variant-numeric: tabular-nums;
}

.char-count.is-short {
  color: var(--ocop-warning-strong);
}

.field-error {
  margin: var(--ocop-space-1) 0 0;
  color: var(--ocop-danger-strong);
  font-size: var(--ocop-font-size-small);
  font-weight: 600;
}

.comment-field textarea {
  min-height: calc(var(--ocop-control-lg) * 2.5);
  resize: vertical;
}

.form-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--ocop-space-2);
}

.form-actions button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
