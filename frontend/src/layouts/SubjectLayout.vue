<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppIcon from '@/components/ui/AppIcon.vue'
import { authStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const isMobileOpen = ref(false)

const pageTitle = computed(() =>
  typeof route.meta.title === 'string' ? route.meta.title : 'Cổng chủ thể',
)

const userInitial = computed(() =>
  authStore.currentUser.value?.full_name.trim().charAt(0).toUpperCase() || 'C',
)

const nav = [
  { label: 'Sản phẩm', icon: 'package', to: '/chu-the/san-pham' },
  { label: 'Điểm du lịch', icon: 'map-pin', to: '/chu-the/diem-du-lich' },
  { label: 'Hồ sơ đơn vị', icon: 'building', to: '/chu-the/ho-so' },
]

function closeMenu(): void {
  isMobileOpen.value = false
}

function onKeydown(e: KeyboardEvent): void {
  if (e.key === 'Escape') closeMenu()
}

async function logout(): Promise<void> {
  authStore.logout()
  await router.push('/dang-nhap')
}

watch(() => route.fullPath, closeMenu)
onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div class="sl-shell">
    <!-- Backdrop mobile -->
    <button
      v-if="isMobileOpen"
      class="sl-backdrop"
      type="button"
      aria-label="Đóng menu"
      @click="closeMenu"
    />

    <!-- ══════════ SIDEBAR ══════════ -->
    <aside id="subject-sidebar" class="sl-sidebar" :class="{ 'is-open': isMobileOpen }">
      <!-- Brand -->
      <RouterLink class="sl-brand" to="/chu-the/san-pham" @click="closeMenu">
        <span class="sl-brand__icon">
          <img src="/assets/figma/home/icon-brand.svg" alt="" />
        </span>
        <span class="sl-brand__text">
          <strong>OCOP LÂM ĐỒNG</strong>
          <small>Cổng quản lý chủ thể</small>
        </span>
      </RouterLink>

      <!-- Nav -->
      <nav class="sl-nav" aria-label="Điều hướng chủ thể">
        <span class="sl-nav__section">QUẢN LÝ</span>
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          class="sl-nav__item"
          :to="item.to"
          @click="closeMenu"
        >
          <span class="sl-nav__icon"><AppIcon :name="item.icon" :size="17" /></span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <!-- Sidebar footer -->
      <div class="sl-sidebar__footer">
        <div class="sl-user">
          <div class="sl-user__avatar">{{ userInitial }}</div>
          <div class="sl-user__info">
            <strong>{{ authStore.currentUser.value?.full_name }}</strong>
            <small>Chủ thể</small>
          </div>
        </div>
        <div class="sl-footer-actions">
          <RouterLink class="sl-footer-btn" to="/">
            <AppIcon name="arrowLeft" :size="13" />
            <span>Trang công khai</span>
          </RouterLink>
          <button class="sl-footer-btn is-danger" type="button" @click="logout">
            <AppIcon name="logout" :size="13" />
            <span>Đăng xuất</span>
          </button>
        </div>
      </div>
    </aside>

    <!-- ══════════ MAIN ══════════ -->
    <div class="sl-main">
      <!-- Topbar -->
      <header class="sl-topbar">
        <button
          class="sl-topbar__toggle"
          type="button"
          :aria-expanded="isMobileOpen"
          aria-controls="subject-sidebar"
          aria-label="Mở hoặc đóng menu"
          @click="isMobileOpen = !isMobileOpen"
        >
          <AppIcon name="menu" :size="20" />
        </button>
        <div class="sl-topbar__title">
          <span>Cổng chủ thể OCOP</span>
          <strong>{{ pageTitle }}</strong>
        </div>
        <RouterLink class="sl-topbar__avatar" to="/chu-the/ho-so">
          <div class="sl-topbar__initial">{{ userInitial }}</div>
          <span>{{ authStore.currentUser.value?.full_name }}</span>
        </RouterLink>
      </header>

      <!-- Content -->
      <div class="sl-content">
        <RouterView />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Shell ── */
.sl-shell {
  display: grid;
  min-height: 100vh;
  grid-template-columns: var(--admin-sidebar-width) minmax(0, 1fr);
  background: var(--admin-bg);
  font-family: var(--admin-font);
}

/* ── Backdrop mobile ── */
.sl-backdrop {
  position: fixed;
  z-index: 45;
  inset: 0;
  border: 0;
  background: rgba(30, 42, 71, 0.48);
  backdrop-filter: blur(2px);
}

/* ══════════ SIDEBAR ══════════ */
.sl-sidebar {
  position: sticky;
  z-index: 50;
  top: 0;
  display: flex;
  height: 100vh;
  flex-direction: column;
  overflow-y: auto;
  padding: 20px 12px 16px;
  background: var(--admin-sidebar-bg);
  scrollbar-width: none;
}
.sl-sidebar::-webkit-scrollbar { display: none; }

/* Brand */
.sl-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px 18px;
  border-bottom: 1px solid rgba(232, 237, 248, 0.10);
  color: #fff;
  text-decoration: none;
}
.sl-brand__icon {
  display: grid;
  width: 36px; height: 36px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 10px;
  background: rgba(47, 107, 255, 0.30);
}
.sl-brand__icon img { width: 20px; height: 20px; }
.sl-brand__text { display: grid; }
.sl-brand__text strong { font-size: 13px; font-weight: 700; letter-spacing: 0.01em; }
.sl-brand__text small { font-size: 11px; color: var(--admin-muted-on-dark); margin-top: 1px; }

/* Nav */
.sl-nav { display: flex; flex: 1; flex-direction: column; gap: 2px; margin-top: 20px; }
.sl-nav__section { padding: 0 10px 6px; color: var(--admin-muted-on-dark); font-size: 10px; font-weight: 700; letter-spacing: 0.08em; }
.sl-nav__item {
  display: flex;
  min-height: 40px;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: var(--admin-radius-md);
  background: transparent;
  color: rgba(232, 237, 248, 0.70);
  font-size: var(--admin-font-sm);
  font-weight: 600;
  text-decoration: none;
  transition: background var(--admin-transition), color var(--admin-transition);
}
.sl-nav__item:hover { background: var(--admin-sidebar-hover); color: #fff; }
.sl-nav__item.router-link-active { background: var(--admin-primary-soft); color: var(--admin-primary); font-weight: 700; }
.sl-nav__icon {
  display: grid;
  width: 28px; height: 28px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 8px;
  background: rgba(232, 237, 248, 0.08);
  color: rgba(232, 237, 248, 0.55);
  transition: color var(--admin-transition);
}
.sl-nav__item:hover .sl-nav__icon { background: rgba(47, 107, 255, 0.18); color: #fff; }
.sl-nav__item.router-link-active .sl-nav__icon { color: var(--admin-primary); background: rgba(47, 107, 255, 0.12); }

/* Sidebar footer */
.sl-sidebar__footer { margin-top: auto; padding-top: 14px; border-top: 1px solid rgba(232, 237, 248, 0.10); display: grid; gap: 10px; }
.sl-user { display: flex; align-items: center; gap: 9px; }
.sl-user__avatar { display: grid; width: 34px; height: 34px; flex-shrink: 0; place-items: center; border-radius: 50%; background: var(--admin-primary); color: #fff; font-size: 13px; font-weight: 800; }
.sl-user__info { display: grid; overflow: hidden; }
.sl-user__info strong { font-size: 13px; color: var(--admin-text-on-dark); font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sl-user__info small { font-size: 11px; color: var(--admin-muted-on-dark); }
.sl-footer-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.sl-footer-btn {
  display: flex; align-items: center; justify-content: center;
  gap: 5px; padding: 8px 6px;
  border: 1px solid rgba(232, 237, 248, 0.14);
  border-radius: var(--admin-radius-sm);
  background: transparent;
  color: var(--admin-text-on-dark);
  font-size: 11px; font-weight: 600;
  text-decoration: none; cursor: pointer;
  transition: background var(--admin-transition);
}
.sl-footer-btn:hover { background: rgba(232, 237, 248, 0.08); }
.sl-footer-btn.is-danger { color: #fca5a5; }
.sl-footer-btn.is-danger:hover { background: rgba(239, 68, 68, 0.12); border-color: rgba(239, 68, 68, 0.24); }

/* ══════════ MAIN ══════════ */
.sl-main { min-width: 0; }

/* Topbar */
.sl-topbar {
  position: sticky; z-index: 30; top: 0;
  display: flex;
  min-height: var(--admin-topbar-height);
  align-items: center;
  gap: 12px;
  padding: 0 24px;
  background: var(--admin-topbar-bg);
  border-bottom: 1px solid var(--admin-border);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}
.sl-topbar__toggle {
  display: none;
  width: 36px; height: 36px;
  flex-shrink: 0;
  place-items: center;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-card);
  color: var(--admin-text);
  cursor: pointer;
}
.sl-topbar__title { display: grid; gap: 1px; }
.sl-topbar__title span { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--admin-muted); }
.sl-topbar__title strong { font-size: var(--admin-font-lg); font-weight: 700; color: var(--admin-text); }
.sl-topbar__avatar {
  display: flex; align-items: center; gap: 8px;
  margin-left: auto;
  padding: 5px 8px;
  border-radius: var(--admin-radius-md);
  color: var(--admin-text); text-decoration: none;
  transition: background var(--admin-transition);
}
.sl-topbar__avatar:hover { background: var(--admin-primary-soft); }
.sl-topbar__initial {
  display: grid; width: 32px; height: 32px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 50%;
  background: var(--admin-primary);
  color: #fff;
  font-size: 13px; font-weight: 800;
}
.sl-topbar__avatar > span { font-size: var(--admin-font-sm); font-weight: 600; }

/* Content */
.sl-content {
  width: min(100%, 1280px);
  margin-inline: auto;
  padding: 28px;
}

/* ── Responsive ── */
@media (max-width: 767.98px) {
  .sl-shell { grid-template-columns: 1fr; }
  .sl-sidebar {
    position: fixed; left: 0; top: 0;
    width: min(var(--admin-sidebar-width), 85vw);
    transform: translateX(-110%);
    transition: transform 220ms cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: var(--admin-shadow-modal);
  }
  .sl-sidebar.is-open { transform: translateX(0); }
  .sl-topbar__toggle { display: grid; }
  .sl-topbar__avatar > span { display: none; }
  .sl-content { padding: 20px 16px; }
}
</style>
