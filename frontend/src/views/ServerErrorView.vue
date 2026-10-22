<script setup lang="ts">
import AppIcon from '@/components/ui/AppIcon.vue'
import ErrorPage from '@/components/ui/ErrorPage.vue'

/** Trang lỗi chung khi một trang gặp lỗi hiển thị bất ngờ (không phải lỗi API đã có khối "Thử lại"). */
function reloadPage(): void {
  window.location.reload()
}
</script>

<template>
  <ErrorPage code="Lỗi" title="Đã xảy ra sự cố" title-id="server-error-title">
    <template #icon>
      <span class="error-icon" aria-hidden="true"><AppIcon name="alert" :size="42" /></span>
    </template>
    <p>Trang này gặp lỗi khi hiển thị. Dữ liệu của bạn không bị mất. Hãy tải lại trang hoặc quay về trang chủ.</p>
    <template #actions>
      <button class="primary-action" type="button" @click="reloadPage">
        <AppIcon name="refresh" :size="14" /> Tải lại trang
      </button>
      <a href="/">Về trang chủ</a>
    </template>
  </ErrorPage>
</template>

<style scoped>
.error-icon {
  display: block;
  margin: var(--ocop-space-3) 0 0;
  color: var(--ocop-tone-berry);
}
</style>
