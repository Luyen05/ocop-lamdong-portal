<script setup lang="ts">
import { useRouter } from 'vue-router'

import { authStore } from '@/stores/auth'

const router = useRouter()
const currentUser = authStore.currentUser
const isAuthenticated = authStore.isAuthenticated

async function logout(): Promise<void> {
  authStore.logout()
  await router.push('/')
}
</script>

<template>
  <header class="site-header">
    <div class="container header-inner">
      <RouterLink class="site-brand" to="/" aria-label="OCOP Lâm Đồng - Trang chủ">
        <span class="brand-symbol">O</span>
        <span class="brand-copy">
          <strong>OCOP Lâm Đồng</strong>
          <small>Đặc sản từ cao nguyên</small>
        </span>
      </RouterLink>

      <nav class="main-nav" aria-label="Điều hướng chính">
        <RouterLink to="/">Trang chủ</RouterLink>
        <a href="#san-pham">Sản phẩm</a>
        <a href="#dia-diem">Điểm đến</a>
      </nav>

      <div v-if="isAuthenticated" class="account-actions">
        <RouterLink class="user-link" to="/tai-khoan">
          <span class="user-avatar">{{ currentUser?.full_name.charAt(0).toUpperCase() }}</span>
          <span class="d-none d-md-inline">{{ currentUser?.full_name }}</span>
        </RouterLink>
        <button class="btn btn-sm btn-outline-success" type="button" @click="logout">
          Đăng xuất
        </button>
      </div>
      <div v-else class="account-actions">
        <RouterLink class="btn btn-sm btn-link text-success text-decoration-none" to="/dang-nhap">
          Đăng nhập
        </RouterLink>
        <RouterLink class="btn btn-sm btn-success px-3" to="/dang-ky">Đăng ký</RouterLink>
      </div>
    </div>
  </header>
</template>

<style scoped>
.site-header {
  position: sticky;
  z-index: 100;
  top: 0;
  border-bottom: 1px solid rgb(29 72 39 / 10%);
  background: rgb(255 255 255 / 92%);
  backdrop-filter: blur(14px);
}

.header-inner {
  display: flex;
  min-height: 4.5rem;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.site-brand,
.user-link {
  display: inline-flex;
  align-items: center;
  color: #17351f;
  text-decoration: none;
}

.site-brand {
  gap: 0.65rem;
}

.brand-symbol,
.user-avatar {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  background: #2f6f3e;
  color: #fff;
  font-weight: 750;
}

.brand-symbol {
  width: 2.4rem;
  height: 2.4rem;
  font-family: Georgia, serif;
  font-size: 1.3rem;
}

.brand-copy {
  display: grid;
  line-height: 1.1;
}

.brand-copy small {
  margin-top: 0.25rem;
  color: #768078;
  font-size: 0.66rem;
}

.main-nav {
  display: none;
  gap: 1.5rem;
}

.main-nav a {
  color: #536057;
  font-size: 0.93rem;
  font-weight: 600;
  text-decoration: none;
}

.main-nav a:hover,
.main-nav a.router-link-active {
  color: #2f6f3e;
}

.account-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.user-link {
  gap: 0.5rem;
  max-width: 12rem;
  font-size: 0.9rem;
  font-weight: 650;
}

.user-avatar {
  width: 2rem;
  height: 2rem;
}

@media (min-width: 992px) {
  .main-nav {
    display: flex;
  }
}

@media (max-width: 575.98px) {
  .brand-copy small,
  .account-actions .btn-link {
    display: none;
  }
}
</style>
