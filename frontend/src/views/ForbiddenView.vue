<script setup lang="ts">
import { computed } from 'vue'

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
      <span class="lock-icon" aria-hidden="true">🔒</span>
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
  padding: 48px 16px;
  place-items: center;
  background:
    radial-gradient(circle at 50% 10%, rgb(164 244 207 / 40%), transparent 24rem),
    var(--ocop-surface);
}

.forbidden-card {
  width: min(100%, 560px);
  padding: clamp(32px, 6vw, 56px);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-xl);
  background: #fff;
  box-shadow: 0 24px 50px rgb(15 23 43 / 10%);
  text-align: center;
}

.error-code {
  display: block;
  color: var(--ocop-primary-700);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.15em;
}

.lock-icon {
  display: block;
  margin: 12px 0;
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
  margin: 16px auto 0;
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
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
}

.forbidden-actions .primary-action {
  border-color: var(--ocop-primary-700);
  background: var(--ocop-primary-700);
  color: #fff;
}
</style>
