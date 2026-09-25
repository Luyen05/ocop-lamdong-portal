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
.subject-sidebar { position: sticky; top: 0; display: flex; height: 100vh; padding: var(--ocop-space-5) var(--ocop-space-4); flex-direction: column; background: var(--ocop-sidebar); color: var(--ocop-text-on-dark); }
.subject-brand { display: flex; padding: 0 var(--ocop-space-2) var(--ocop-space-5); align-items: center; gap: 10px; border-bottom: 1px solid color-mix(in srgb, var(--ocop-white) 12%, transparent); color: var(--ocop-white); text-decoration: none; }
.subject-brand > span { display: grid; width: 38px; height: 38px; place-items: center; border-radius: 10px; background: var(--ocop-primary-700); }
.subject-brand img { width: 22px; }
.subject-brand div, .subject-page-heading, .subject-account div { display: grid; }
.subject-brand strong { font-size: var(--ocop-font-size-small); }
.subject-brand small { color: var(--ocop-sidebar-muted); font-size: var(--ocop-font-size-caption); }
.subject-topbar small, .subject-account small { color: var(--ocop-text-secondary); font-size: var(--ocop-font-size-caption); }
.subject-sidebar nav { display: grid; margin-top: var(--ocop-space-6); gap: 6px; }
.subject-sidebar nav a { display: flex; padding: 11px var(--ocop-space-3); align-items: center; gap: 10px; border: 1px solid transparent; border-radius: 9px; color: var(--ocop-sidebar-muted); font-size: var(--ocop-font-size-small); font-weight: 700; text-decoration: none; }
.subject-sidebar nav a :deep(.app-icon) { color: var(--ocop-mint-300); }
.subject-sidebar nav a:hover, .subject-sidebar nav a.router-link-active { border-color: color-mix(in srgb, var(--ocop-mint) 24%, transparent); background: color-mix(in srgb, var(--ocop-primary-500) 22%, transparent); color: var(--ocop-white); }
.subject-sidebar-footer { display: grid; margin-top: auto; gap: var(--ocop-space-2); }
.subject-sidebar-footer a, .subject-sidebar-footer button { display: flex; padding: 9px; align-items: center; justify-content: center; gap: 7px; border: 1px solid color-mix(in srgb, var(--ocop-white) 14%, transparent); border-radius: var(--ocop-radius-sm); background: transparent; color: var(--ocop-text-on-dark); font-size: var(--ocop-font-size-caption); text-align: center; text-decoration: none; }
.subject-main { min-width: 0; }
.subject-topbar { display: flex; min-height: 72px; padding: var(--ocop-space-3) 28px; align-items: center; border-bottom: 1px solid var(--ocop-border); background: var(--ocop-card); }
.subject-topbar > div strong { color: var(--ocop-navy); font-size: var(--ocop-font-size-body-lg); }
.subject-account { display: flex; margin-left: auto; align-items: center; gap: var(--ocop-space-2); color: var(--ocop-navy); text-decoration: none; }
.subject-account > span { display: grid; width: 36px; height: 36px; place-items: center; border-radius: 50%; background: var(--ocop-primary-700); color: var(--ocop-white); font-size: var(--ocop-font-size-caption); font-weight: 800; }
.subject-account div strong { font-size: var(--ocop-font-size-caption); }
.subject-mobile-actions { display: none; }
.subject-content { width: min(100%, 1280px); margin-inline: auto; padding: 28px; }
@media (max-width: 767.98px) {
  .subject-shell { grid-template-columns: 1fr; }
  .subject-sidebar { position: static; width: 100%; height: auto; }
  .subject-sidebar nav { grid-template-columns: 1fr 1fr; margin-top: 14px; }
  .subject-sidebar-footer { display: none; }
  .subject-topbar { padding-inline: var(--ocop-space-4); }
  .subject-account { display: none; }
  .subject-mobile-actions { display: flex; margin-left: auto; align-items: center; gap: 6px; }
  .subject-mobile-actions a, .subject-mobile-actions button { display: grid; width: 34px; height: 34px; padding: 0; place-items: center; border: 1px solid var(--ocop-border); border-radius: var(--ocop-radius-sm); background: var(--ocop-card); color: var(--ocop-primary-900); text-decoration: none; }
  .subject-content { padding: var(--ocop-space-5) var(--ocop-space-4); }
}
</style>
