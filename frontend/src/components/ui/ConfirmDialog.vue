<script setup lang="ts">
import { computed, ref, toRef, useId } from 'vue'

import { useDialogFocus } from '@/composables/useDialogFocus'

const props = withDefaults(
  defineProps<{
    open: boolean
    title: string
    /** Nội dung ngắn; cần định dạng phức tạp hơn thì dùng slot mặc định. */
    message?: string
    confirmLabel?: string
    cancelLabel?: string
    /** `danger` cho thao tác xóa, hủy, từ chối; `primary` cho thao tác thường. */
    tone?: 'danger' | 'primary'
    /** Đang xử lý: khóa hai nút, không đóng được bằng Esc hay bấm nền. */
    busy?: boolean
    busyLabel?: string
  }>(),
  {
    message: '',
    confirmLabel: 'Xác nhận',
    cancelLabel: 'Hủy',
    tone: 'primary',
    busy: false,
    busyLabel: 'Đang xử lý...',
  },
)

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

const uid = useId()
const titleId = `confirm-title-${uid}`
const descId = `confirm-desc-${uid}`
const dialogRef = ref<HTMLElement | null>(null)

function requestCancel(): void {
  if (!props.busy) emit('cancel')
}

// Nút "Hủy" đứng trước trong DOM nên là phần tử được focus đầu tiên (lựa chọn an toàn).
useDialogFocus(toRef(props, 'open'), dialogRef, requestCancel)

const confirmText = computed(() => (props.busy ? props.busyLabel : props.confirmLabel))
</script>

<template>
  <Transition name="ocop-fade">
    <div v-if="open" class="cd-layer" role="presentation" @click.self="requestCancel">
      <div
        ref="dialogRef"
        class="cd-dialog"
        role="alertdialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        :aria-describedby="descId"
        tabindex="-1"
        @keydown.stop
      >
        <h2 :id="titleId">{{ title }}</h2>
        <div :id="descId" class="cd-body">
          <slot><p v-if="message">{{ message }}</p></slot>
        </div>
        <div class="cd-actions">
          <button class="cd-btn" type="button" :disabled="busy" @click="requestCancel">{{ cancelLabel }}</button>
          <button
            class="cd-btn cd-btn--confirm"
            :class="{ 'is-danger': tone === 'danger' }"
            type="button"
            :disabled="busy"
            :aria-busy="busy"
            @click="emit('confirm')"
          >{{ confirmText }}</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.cd-layer {
  position: fixed;
  z-index: 200;
  inset: 0;
  display: grid;
  padding: var(--admin-space-5);
  place-items: center;
  overflow-y: auto;
  background: var(--admin-scrim);
}
.cd-dialog {
  width: min(100%, 460px);
  padding: var(--admin-space-6);
  border-radius: var(--admin-radius-lg);
  background: var(--admin-card);
  box-shadow: var(--admin-shadow-modal);
  font-family: var(--admin-font);
}
.cd-dialog h2 { margin: 0 0 var(--admin-space-3); color: var(--admin-text); font-size: var(--admin-font-xl); font-weight: 800; }
.cd-body { color: var(--admin-text); font-size: var(--admin-font-sm); line-height: 1.55; overflow-wrap: anywhere; }
.cd-body :deep(p) { margin: 0; }
.cd-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: var(--admin-space-2); margin-top: var(--admin-space-5); }
.cd-btn {
  min-width: 96px;
  min-height: 44px;
  padding: 0 var(--admin-space-4);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-card);
  color: var(--admin-text);
  font-size: var(--admin-font-sm);
  font-weight: 700;
  cursor: pointer;
  transition: background var(--admin-transition), border-color var(--admin-transition);
}
.cd-btn:hover:not(:disabled) { border-color: var(--admin-primary); color: var(--admin-primary-dark); }
.cd-btn:disabled { cursor: not-allowed; opacity: 0.6; }
.cd-btn--confirm { border-color: var(--admin-primary); background: var(--admin-primary-dark); color: var(--admin-on-primary); }
.cd-btn--confirm:hover:not(:disabled) { background: var(--admin-primary-dark); color: var(--admin-on-primary); }
.cd-btn--confirm.is-danger { border-color: var(--admin-danger-text); background: var(--admin-danger-text); color: var(--ocop-white); }
.cd-btn--confirm.is-danger:hover:not(:disabled) { background: var(--admin-danger-hover); color: var(--ocop-white); }
.cd-btn:focus-visible { outline: 3px solid var(--admin-primary-dark); outline-offset: 2px; }
@media (max-width: 480px) {
  .cd-actions { flex-direction: column-reverse; }
  .cd-btn { width: 100%; }
}
@media (prefers-reduced-motion: reduce) {
  .cd-btn { transition: none; }
}
</style>
