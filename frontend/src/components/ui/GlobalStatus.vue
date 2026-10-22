<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import AppIcon from '@/components/ui/AppIcon.vue'
import { pageStatus } from '@/stores/page-status'

/**
 * Thông báo toàn cục ở cuối màn hình:
 * - mất mạng / có mạng trở lại;
 * - không mở được trang (mã trang tải thất bại) kèm nút "Thử lại".
 */
const router = useRouter()
const justReconnected = ref(false)
let reconnectTimer: ReturnType<typeof setTimeout> | undefined

function onOnline(): void {
  pageStatus.setOnline(true)
}

function onOffline(): void {
  pageStatus.setOnline(false)
}

watch(pageStatus.online, (isOnline, wasOnline) => {
  if (isOnline && wasOnline === false) {
    justReconnected.value = true
    clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(() => {
      justReconnected.value = false
    }, 3000)
  } else if (!isOnline) {
    justReconnected.value = false
  }
})

function retryNavigation(): void {
  const target = pageStatus.navigationFailure.value?.target
  pageStatus.dismissNavigationFailure()
  if (target) void router.push(target)
}

onMounted(() => {
  window.addEventListener('online', onOnline)
  window.addEventListener('offline', onOffline)
  pageStatus.setOnline(navigator.onLine !== false)
})

onBeforeUnmount(() => {
  window.removeEventListener('online', onOnline)
  window.removeEventListener('offline', onOffline)
  clearTimeout(reconnectTimer)
})
</script>

<template>
  <div class="global-status" aria-live="polite">
    <div v-if="!pageStatus.online.value" class="global-status__item is-offline" role="status" data-testid="offline-notice">
      <AppIcon name="wifiOff" :size="18" />
      <span>Bạn đang ngoại tuyến. Một số nội dung có thể không tải được.</span>
    </div>
    <div v-else-if="justReconnected" class="global-status__item is-online" role="status" data-testid="online-notice">
      <AppIcon name="checkCircle" :size="18" />
      <span>Đã kết nối lại.</span>
    </div>
    <div
      v-if="pageStatus.navigationFailure.value"
      class="global-status__item is-error"
      role="alert"
      data-testid="navigation-failure"
    >
      <AppIcon name="alert" :size="18" />
      <span>Chưa mở được trang. Kiểm tra kết nối mạng rồi thử lại.</span>
      <button type="button" class="global-status__action" @click="retryNavigation">Thử lại</button>
      <button
        type="button"
        class="global-status__close"
        aria-label="Đóng thông báo"
        @click="pageStatus.dismissNavigationFailure()"
      >
        <AppIcon name="close" :size="14" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.global-status {
  position: fixed;
  z-index: 1999;
  right: var(--ocop-space-4);
  bottom: max(var(--ocop-space-4), env(safe-area-inset-bottom));
  left: var(--ocop-space-4);
  display: grid;
  justify-items: center;
  gap: var(--ocop-space-2);
  pointer-events: none;
}

.global-status__item {
  display: flex;
  max-width: min(100%, 520px);
  align-items: center;
  gap: var(--ocop-space-2);
  padding: 10px 14px;
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-navy);
  box-shadow: 0 12px 28px color-mix(in srgb, var(--ocop-neutral-900) 28%, transparent);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-small);
  pointer-events: auto;
  animation: ocop-rise-in var(--ocop-duration-base) var(--ocop-ease-out) both;
}

.global-status__item.is-online {
  background: var(--ocop-primary-700);
}

.global-status__item.is-error {
  background: var(--ocop-tone-berry);
}

.global-status__action {
  padding: 4px 12px;
  border: 1px solid color-mix(in srgb, var(--ocop-white) 70%, transparent);
  border-radius: var(--ocop-radius-sm);
  background: transparent;
  color: inherit;
  font-weight: 700;
}

.global-status__action:hover {
  background: color-mix(in srgb, var(--ocop-white) 18%, transparent);
}

.global-status__close {
  display: grid;
  width: 24px;
  height: 24px;
  place-items: center;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: inherit;
}

/* Trên điện thoại, thanh tab dưới cùng chiếm chỗ: nâng thông báo lên trên nó. */
@media (max-width: 767.98px) {
  .global-status {
    bottom: calc(var(--ocop-tabbar-height) + var(--ocop-space-3) + env(safe-area-inset-bottom));
  }
}

@media (prefers-reduced-motion: reduce) {
  .global-status__item {
    animation: none;
  }
}
</style>
