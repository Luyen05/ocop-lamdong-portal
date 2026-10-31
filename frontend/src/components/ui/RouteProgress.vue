<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'

import { pageStatus } from '@/stores/page-status'

/**
 * Thanh tiến trình mảnh trên đầu trang khi chuyển trang hoặc chờ dữ liệu.
 * Chỉ hiện sau SHOW_DELAY_MS để thao tác nhanh không bị nhấp nháy; chạy chậm dần tới 90%,
 * khi xong thì đầy 100% rồi mờ đi. Người đọc màn hình nghe thông báo "Đang tải trang…".
 */
const SHOW_DELAY_MS = 150
const TRICKLE_MS = 250
const FINISH_MS = 260

const visible = ref(false)
const progress = ref(0)
const finishing = ref(false)

let showTimer: ReturnType<typeof setTimeout> | undefined
let hideTimer: ReturnType<typeof setTimeout> | undefined
let trickleTimer: ReturnType<typeof setInterval> | undefined

function clearTimers(): void {
  clearTimeout(showTimer)
  clearTimeout(hideTimer)
  clearInterval(trickleTimer)
  showTimer = hideTimer = trickleTimer = undefined
}

function show(): void {
  visible.value = true
  finishing.value = false
  progress.value = 0.08
  trickleTimer = setInterval(() => {
    progress.value += (0.9 - progress.value) * 0.12
  }, TRICKLE_MS)
}

function finish(): void {
  clearInterval(trickleTimer)
  trickleTimer = undefined
  finishing.value = true
  progress.value = 1
  hideTimer = setTimeout(() => {
    visible.value = false
    finishing.value = false
    progress.value = 0
  }, FINISH_MS)
}

watch(
  pageStatus.isBusy,
  (busy) => {
    if (busy) {
      clearTimeout(hideTimer)
      hideTimer = undefined
      if (visible.value && finishing.value) {
        // Việc mới bắt đầu khi thanh đang kết thúc: chạy lại từ đầu.
        clearInterval(trickleTimer)
        show()
      } else if (!visible.value && showTimer === undefined) {
        showTimer = setTimeout(() => {
          showTimer = undefined
          show()
        }, SHOW_DELAY_MS)
      }
      return
    }
    clearTimeout(showTimer)
    showTimer = undefined
    if (visible.value) finish()
  },
  { immediate: true },
)

onBeforeUnmount(clearTimers)
</script>

<template>
  <div class="route-progress-root">
    <div
      v-if="visible"
      class="route-progress"
      :class="{ 'is-finishing': finishing }"
      data-testid="route-progress"
      aria-hidden="true"
    >
      <span class="route-progress__bar" :style="{ transform: `scaleX(${progress})` }" />
    </div>
    <span class="visually-hidden" role="status" aria-live="polite">{{ visible && !finishing ? 'Đang tải trang…' : '' }}</span>
  </div>
</template>

<style scoped>
.route-progress {
  position: fixed;
  z-index: 2000;
  inset: 0 0 auto;
  height: 3px;
  pointer-events: none;
  transition: opacity 220ms ease-out 60ms;
}

.route-progress.is-finishing {
  opacity: 0;
}

.route-progress__bar {
  display: block;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, var(--ocop-primary-700), var(--ocop-accent));
  box-shadow: 0 0 8px color-mix(in srgb, var(--ocop-accent) 70%, transparent);
  transform-origin: left center;
  transition: transform 240ms ease-out;
}

@media (prefers-reduced-motion: reduce) {
  .route-progress,
  .route-progress__bar {
    transition: none;
  }
}
</style>
