<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppIcon from '@/components/ui/AppIcon.vue'
import { authStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const initial = computed(() => authStore.currentUser.value?.full_name.charAt(0).toUpperCase() || 'C')
const pageTitle = computed(() => String(route.meta.title || 'Khu vực chủ thể'))

async function logout(): Promise<void> {
  authStore.logout()
  await router.push('/dang-nhap')
}
</script>

<template>
  <div class="subject-shell">
    <aside class="subject-sidebar">
      <RouterLink class="subject-brand" to="/chu-the/san-pham">
        <span><img src="/assets/figma/home/icon-brand.svg" alt="" /></span>
        <div>
          <strong>LÂM ĐỒNG OCOP</strong>
          <small>Khu vực chủ thể</small>
        </div>
      </RouterLink>
      <nav aria-label="Điều hướng chủ thể">
        <RouterLink to="/chu-the/san-pham"><AppIcon name="package" :size="18" /> Sản phẩm của tôi</RouterLink>
        <RouterLink to="/chu-the/ho-so"><AppIcon name="building" :size="18" /> Hồ sơ chủ thể</RouterLink>
      </nav>
      <div class="subject-sidebar-footer">
        <RouterLink to="/"><AppIcon name="arrowLeft" :size="15" /> Về trang công khai</RouterLink>
        <button type="button" @click="logout"><AppIcon name="logout" :size="15" /> Đăng xuất</button>
      </div>
    </aside>
    <section class="subject-main">
      <header class="subject-topbar">
        <div class="subject-page-heading">
          <small>Quản lý nội dung OCOP</small>
          <strong>{{ pageTitle }}</strong>
        </div>
        <div class="subject-mobile-actions" aria-label="Tiện ích chủ thể">
          <RouterLink to="/tai-khoan" aria-label="Mở trang tài khoản"><AppIcon name="user" :size="16" /></RouterLink>
          <RouterLink to="/" aria-label="Về trang công khai"><AppIcon name="home" :size="16" /></RouterLink>
          <button type="button" aria-label="Đăng xuất" @click="logout"><AppIcon name="logout" :size="16" /></button>
        </div>
        <RouterLink to="/tai-khoan" class="subject-account">
          <span>{{ initial }}</span>
          <div>
            <strong>{{ authStore.currentUser.value?.full_name }}</strong>
            <small>Chủ thể OCOP</small>
          </div>
        </RouterLink>
      </header>
      <div class="subject-content"><RouterView /></div>
    </section>
  </div>
</template>

<style scoped>
.subject-shell { display: grid; min-height: 100vh; grid-template-columns: 250px minmax(0, 1fr); background: var(--ocop-surface); }
.subject-sidebar { position: sticky; top: 0; display: flex; height: 100vh; padding: 20px 16px; flex-direction: column; background: var(--ocop-sidebar); color: #d9e9e4; }
.subject-brand { display: flex; padding: 0 8px 20px; align-items: center; gap: 10px; border-bottom: 1px solid rgb(255 255 255 / 12%); color: #fff; text-decoration: none; }
.subject-brand > span { display: grid; width: 38px; height: 38px; place-items: center; border-radius: 10px; background: var(--ocop-primary-700); }
.subject-brand img { width: 22px; }
.subject-brand div, .subject-page-heading, .subject-account div { display: grid; }
.subject-brand strong { font-size: 13px; }
.subject-brand small, .subject-topbar small, .subject-account small { color: var(--ocop-sidebar-muted); font-size: 10px; }
.subject-sidebar nav { display: grid; margin-top: 24px; gap: 6px; }
.subject-sidebar nav a { display: flex; padding: 11px 12px; align-items: center; gap: 10px; border: 1px solid transparent; border-radius: 9px; color: var(--ocop-sidebar-muted); font-size: 12px; font-weight: 700; text-decoration: none; }
.subject-sidebar nav a :deep(.app-icon) { color: #83d7ad; }
.subject-sidebar nav a:hover, .subject-sidebar nav a.router-link-active { border-color: rgb(102 201 150 / 24%); background: rgb(53 164 117 / 22%); color: #fff; }
.subject-sidebar-footer { display: grid; margin-top: auto; gap: 8px; }
.subject-sidebar-footer a, .subject-sidebar-footer button { display: flex; padding: 9px; align-items: center; justify-content: center; gap: 7px; border: 1px solid rgb(255 255 255 / 14%); border-radius: 8px; background: transparent; color: #d9e9e4; font-size: 11px; text-align: center; text-decoration: none; }
.subject-main { min-width: 0; }
.subject-topbar { display: flex; min-height: 72px; padding: 12px 28px; align-items: center; border-bottom: 1px solid var(--ocop-border); background: #fff; }
.subject-topbar > div strong { color: var(--ocop-navy); font-size: 16px; }
.subject-account { display: flex; margin-left: auto; align-items: center; gap: 8px; color: var(--ocop-navy); text-decoration: none; }
.subject-account > span { display: grid; width: 36px; height: 36px; place-items: center; border-radius: 50%; background: var(--ocop-primary-700); color: #fff; font-size: 12px; font-weight: 800; }
.subject-account div strong { font-size: 12px; }
.subject-mobile-actions { display: none; }
.subject-content { width: min(100%, 1280px); margin-inline: auto; padding: 28px; }
@media (max-width: 767.98px) {
  .subject-shell { grid-template-columns: 1fr; }
  .subject-sidebar { position: static; width: 100%; height: auto; }
  .subject-sidebar nav { grid-template-columns: 1fr 1fr; margin-top: 14px; }
  .subject-sidebar-footer { display: none; }
  .subject-topbar { padding-inline: 16px; }
  .subject-account { display: none; }
  .subject-mobile-actions { display: flex; margin-left: auto; align-items: center; gap: 6px; }
  .subject-mobile-actions a, .subject-mobile-actions button { display: grid; width: 34px; height: 34px; padding: 0; place-items: center; border: 1px solid var(--ocop-border); border-radius: 8px; background: #fff; color: var(--ocop-primary-900); text-decoration: none; }
  .subject-content { padding: 20px 16px; }
}
</style>
