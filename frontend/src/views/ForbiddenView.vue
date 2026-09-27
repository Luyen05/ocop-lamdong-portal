<script setup lang="ts">
import { computed } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
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
  <main class="forbidden-page">
    <section class="forbidden-card" aria-labelledby="forbidden-title">
      <span class="error-code">403</span>
      <span class="lock-icon" aria-hidden="true"><AppIcon name="lock" :size="42" /></span>
      <h1 id="forbidden-title">Bạn không có quyền truy cập</h1>
      <p>
        Tài khoản hiện tại có vai trò <strong>{{ roleLabel }}</strong> và không được phép mở khu vực này.
      </p>
      <div class="forbidden-actions">
        <RouterLink class="primary-action" to="/">Về trang chủ</RouterLink>
        <RouterLink v-if="authStore.isAuthenticated.value" to="/tai-khoan">Xem tài khoản</RouterLink>
        <RouterLink v-else to="/dang-nhap">Đăng nhập</RouterLink>
      </div>
    </section>
  </main>
</template>

<style scoped>
.forbidden-page {
  display: grid;
  min-height: 65vh;
  padding: var(--ocop-space-12) var(--ocop-space-4);
  place-items: center;
  background:
    radial-gradient(circle at 50% 10%, color-mix(in srgb, var(--ocop-mint-200) 40%, transparent), transparent 24rem),
    var(--ocop-surface);
}

.forbidden-card {
  width: min(100%, 560px);
  padding: clamp(var(--ocop-space-8), 6vw, 56px);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-xl);
  background: var(--ocop-card);
  box-shadow: 0 24px 50px color-mix(in srgb, var(--ocop-neutral-900) 10%, transparent);
  text-align: center;
}

.error-code {
  display: block;
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-caption);
  font-weight: 800;
  letter-spacing: 0.15em;
}

.lock-icon {
  display: block;
  margin: var(--ocop-space-3) 0;
  font-size: 42px;
}

h1 {
  margin: 0;
  color: var(--ocop-navy);
  font-size: clamp(28px, 5vw, 38px);
  font-weight: 800;
  letter-spacing: -0.7px;
}

p {
  margin: var(--ocop-space-4) auto 0;
  color: var(--ocop-slate);
  line-height: 1.7;
}

.forbidden-actions {
  display: flex;
  margin-top: 28px;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.forbidden-actions a {
  padding: 10px 18px;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-md);
  color: var(--ocop-primary-900);
  font-size: var(--ocop-font-size-small);
  font-weight: 700;
  text-decoration: none;
}

.forbidden-actions .primary-action {
  border-color: var(--ocop-primary-700);
  background: var(--ocop-primary-700);
  color: var(--ocop-white);
}
</style>
