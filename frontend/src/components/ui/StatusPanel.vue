<script setup lang="ts">
import { computed } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'

/**
 * Khối trạng thái dùng chung cho danh sách và trang chi tiết: đang tải (khung xương),
 * lỗi (có nút "Thử lại") và rỗng. Dùng ở khu quản trị, chủ thể và trang công khai để mọi
 * trang báo trạng thái giống nhau.
 */
const props = withDefaults(
  defineProps<{
    kind: 'loading' | 'error' | 'empty'
    title?: string
    message?: string
    rows?: number
    retryLabel?: string
    retryable?: boolean
  }>(),
  { title: '', message: '', rows: 3, retryLabel: 'Thử lại', retryable: true },
)

const emit = defineEmits<{ retry: [] }>()

const heading = computed(() => {
  if (props.title) return props.title
  if (props.kind === 'error') return 'Chưa tải được dữ liệu'
  if (props.kind === 'empty') return 'Chưa có dữ liệu'
  return ''
})
</script>

<template>
  <div v-if="kind === 'loading'" class="status-panel is-loading" role="status" aria-live="polite">
    <span class="visually-hidden">{{ message || 'Đang tải dữ liệu…' }}</span>
    <div v-for="index in rows" :key="index" class="skeleton-row" aria-hidden="true">
      <span class="ocop-skeleton skeleton-thumb" />
      <span class="skeleton-lines">
        <span class="ocop-skeleton skeleton-line" />
        <span class="ocop-skeleton skeleton-line is-short" />
      </span>
    </div>
  </div>

  <div v-else class="status-panel" :class="`is-${kind}`" :role="kind === 'error' ? 'alert' : 'status'">
    <span class="status-icon" aria-hidden="true">
      <AppIcon :name="kind === 'error' ? 'alert' : 'search'" :size="22" />
    </span>
    <p class="status-title">{{ heading }}</p>
    <p v-if="message" class="status-message">{{ message }}</p>
    <button v-if="kind === 'error' && retryable" class="status-retry" type="button" @click="emit('retry')">
      <AppIcon name="refresh" :size="16" /> {{ retryLabel }}
    </button>
    <slot />
  </div>
</template>

<style scoped>
.status-panel {
  display: grid;
  justify-items: center;
  gap: var(--ocop-space-2);
  padding: var(--ocop-space-8) var(--ocop-space-4);
  color: var(--ocop-slate);
  text-align: center;
  animation: ocop-fade-in var(--ocop-duration-base) var(--ocop-ease-out) both;
}

.status-panel.is-loading {
  justify-items: stretch;
  gap: var(--ocop-space-3);
  padding: var(--ocop-space-4);
  text-align: left;
}

.status-icon {
  display: grid;
  width: 48px;
  height: 48px;
  place-items: center;
  border-radius: 50%;
  background: var(--ocop-mist-100);
  color: var(--ocop-mist-700);
}

.is-error .status-icon {
  background: var(--ocop-tone-berry-soft);
  color: var(--ocop-tone-berry);
}

.status-title {
  margin: 0;
  color: var(--ocop-mist-950);
  font-weight: 700;
}

.status-message {
  max-width: 46ch;
  margin: 0;
  font-size: var(--ocop-font-size-body);
}

.status-retry {
  display: inline-flex;
  min-height: var(--ocop-control-md);
  align-items: center;
  gap: var(--ocop-space-2);
  margin-top: var(--ocop-space-2);
  padding: 0 var(--ocop-space-4);
  border: 1px solid var(--ocop-mist-300);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-white);
  color: var(--ocop-mist-950);
  font-weight: 600;
  transition: border-color var(--ocop-transition), background var(--ocop-transition);
}

.status-retry:hover {
  border-color: var(--ocop-mist-600);
  background: var(--ocop-mist-50);
}

.skeleton-row {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr);
  align-items: center;
  gap: var(--ocop-space-3);
}

.skeleton-thumb {
  height: 56px;
  border-radius: var(--ocop-radius-md);
}

.skeleton-lines {
  display: grid;
  gap: var(--ocop-space-2);
}

.skeleton-line {
  height: 12px;
}

.skeleton-line.is-short {
  width: 55%;
}
</style>
