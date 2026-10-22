<script setup lang="ts">
/**
 * Khung xương cả trang, hiện khi chưa có trang nào được dựng (lần mở đầu tiên, đang chờ
 * kiểm tra đăng nhập hoặc tải mã trang). Giữ đúng chiều cao một màn hình nên chân trang không nhảy.
 */
defineProps<{ label?: string }>()
</script>

<template>
  <div class="page-skeleton" role="status" aria-live="polite" data-testid="page-skeleton">
    <span class="visually-hidden">{{ label || 'Đang tải trang…' }}</span>
    <div class="page-skeleton__inner" aria-hidden="true">
      <span class="ocop-skeleton page-skeleton__crumb" />
      <span class="ocop-skeleton page-skeleton__title" />
      <span class="ocop-skeleton page-skeleton__lead" />
      <div class="page-skeleton__grid">
        <div v-for="index in 6" :key="index" class="page-skeleton__card">
          <span class="ocop-skeleton page-skeleton__image" />
          <span class="ocop-skeleton page-skeleton__line" />
          <span class="ocop-skeleton page-skeleton__line is-short" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-skeleton {
  padding: var(--ocop-space-8) var(--ocop-space-4);
}

.page-skeleton__inner {
  display: grid;
  width: min(100%, 1180px);
  margin: 0 auto;
  gap: var(--ocop-space-4);
}

.page-skeleton__crumb {
  width: 180px;
  height: 14px;
}

.page-skeleton__title {
  width: min(100%, 420px);
  height: 36px;
}

.page-skeleton__lead {
  width: min(100%, 640px);
  height: 16px;
}

.page-skeleton__grid {
  display: grid;
  margin-top: var(--ocop-space-4);
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--ocop-space-4);
}

.page-skeleton__card {
  display: grid;
  gap: var(--ocop-space-2);
  padding: var(--ocop-space-3);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
}

.page-skeleton__image {
  height: 150px;
  border-radius: var(--ocop-radius-md);
}

.page-skeleton__line {
  height: 12px;
}

.page-skeleton__line.is-short {
  width: 55%;
}
</style>
