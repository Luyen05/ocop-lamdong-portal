<script setup lang="ts">
import { computed } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import ErrorPage from '@/components/ui/ErrorPage.vue'
import { authStore } from '@/stores/auth'

const roleLabel = computed(() => {
  const labels = {
    admin: 'Quản trị viên',
    subject: 'Chủ thể OCOP',
    user: 'Người dùng',
  }
  return authStore.currentUser.value ? labels[authStore.currentUser.value.role] : 'Khách'
})
</script>

<template>
  <ErrorPage code="403" title="Bạn không có quyền truy cập" title-id="forbidden-title">
    <template #icon>
      <span class="lock-icon" aria-hidden="true"><AppIcon name="lock" :size="42" /></span>
    </template>
    <p>
      Tài khoản hiện tại có vai trò <strong>{{ roleLabel }}</strong> và không được phép mở khu vực này.
    </p>
    <template #actions>
      <RouterLink class="primary-action" to="/">Về trang chủ</RouterLink>
      <RouterLink v-if="authStore.isAuthenticated.value" to="/tai-khoan">Xem tài khoản</RouterLink>
      <RouterLink v-else to="/dang-nhap">Đăng nhập</RouterLink>
    </template>
  </ErrorPage>
</template>

<style scoped>
.lock-icon {
  display: block;
  margin: var(--ocop-space-3) 0 0;
  color: var(--ocop-primary-700);
}
</style>
