<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { authStore } from '@/stores/auth'

const router = useRouter()
const initial = computed(() => authStore.currentUser.value?.full_name.charAt(0).toUpperCase() || 'C')

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
        <RouterLink to="/chu-the/san-pham">◈ Sản phẩm của tôi</RouterLink>
        <RouterLink to="/dang-ky-chu-the">♢ Hồ sơ chủ thể</RouterLink>
      </nav>
      <div class="subject-sidebar-footer">
        <RouterLink to="/">← Về trang công khai</RouterLink>
        <button type="button" @click="logout">Đăng xuất</button>
      </div>
    </aside>
    <section class="subject-main">
      <header class="subject-topbar">
        <div>
          <small>Quản lý nội dung OCOP</small>
          <strong>Sản phẩm của chủ thể</strong>
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
.subject-shell { display: grid; min-height: 100vh; grid-template-columns: 250px minmax(0, 1fr); background: #f4f7f6; }
.subject-sidebar { position: sticky; top: 0; display: flex; height: 100vh; padding: 20px 16px; flex-direction: column; background: #0f2f29; color: #d9e9e4; }
.subject-brand { display: flex; padding: 0 8px 20px; align-items: center; gap: 10px; border-bottom: 1px solid rgb(255 255 255 / 12%); color: #fff; text-decoration: none; }
.subject-brand > span { display: grid; width: 38px; height: 38px; place-items: center; border-radius: 10px; background: var(--ocop-primary-700); }
.subject-brand img { width: 22px; }
.subject-brand div, .subject-topbar > div, .subject-account div { display: grid; }
.subject-brand strong { font-size: 13px; }
.subject-brand small, .subject-topbar small, .subject-account small { color: #91aaa3; font-size: 10px; }
.subject-sidebar nav { display: grid; margin-top: 24px; gap: 6px; }
.subject-sidebar nav a { padding: 11px 12px; border-radius: 9px; color: #bcd0ca; font-size: 12px; font-weight: 700; text-decoration: none; }
.subject-sidebar nav a:hover, .subject-sidebar nav a.router-link-active { background: rgb(0 122 85 / 32%); color: #fff; }
.subject-sidebar-footer { display: grid; margin-top: auto; gap: 8px; }
.subject-sidebar-footer a, .subject-sidebar-footer button { padding: 9px; border: 1px solid rgb(255 255 255 / 14%); border-radius: 8px; background: transparent; color: #d9e9e4; font-size: 11px; text-align: center; text-decoration: none; }
.subject-main { min-width: 0; }
.subject-topbar { display: flex; min-height: 72px; padding: 12px 28px; align-items: center; border-bottom: 1px solid var(--ocop-border); background: #fff; }
.subject-topbar > div strong { color: var(--ocop-navy); font-size: 16px; }
.subject-account { display: flex; margin-left: auto; align-items: center; gap: 8px; color: var(--ocop-navy); text-decoration: none; }
.subject-account > span { display: grid; width: 36px; height: 36px; place-items: center; border-radius: 50%; background: var(--ocop-primary-700); color: #fff; font-size: 12px; font-weight: 800; }
.subject-account div strong { font-size: 12px; }
.subject-content { width: min(100%, 1280px); margin-inline: auto; padding: 28px; }
@media (max-width: 767.98px) {
  .subject-shell { grid-template-columns: 1fr; }
  .subject-sidebar { position: static; width: 100%; height: auto; }
  .subject-sidebar nav { grid-template-columns: 1fr 1fr; margin-top: 14px; }
  .subject-sidebar-footer { display: none; }
  .subject-topbar { padding-inline: 16px; }
  .subject-account div { display: none; }
  .subject-content { padding: 20px 16px; }
}
</style>
