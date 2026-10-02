<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppIcon from '@/components/ui/AppIcon.vue'
import { authStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const isSidebarOpen = ref(false)

const userInitial = computed(() =>
  authStore.currentUser.value?.full_name.trim().charAt(0).toUpperCase() || 'A',
)

const pageTitle = computed(() =>
  typeof route.meta.title === 'string' ? route.meta.title : 'Tổng quan quản trị',
)

const navigation = [
  { label: 'Tổng quan', icon: 'dashboard', to: '/quan-tri', available: true },
  { label: 'Sản phẩm', icon: 'package', to: '/quan-tri/san-pham', available: true },
  { label: 'Điểm du lịch', icon: 'map-pin', to: '/quan-tri/diem-du-lich', available: true },
  { label: 'Chủ thể / HTX', icon: 'building', to: '/quan-tri/ho-so-chu-the', available: true },
  { label: 'Người dùng', icon: 'users', to: '', available: false },
  { label: 'Đánh giá', icon: 'star', to: '', available: false },
  { label: 'Bài viết', icon: 'newspaper', to: '', available: false },
]

function closeSidebar(): void {
  isSidebarOpen.value = false
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') closeSidebar()
}

async function logout(): Promise<void> {
  authStore.logout()
  await router.push('/dang-nhap')
}

watch(() => route.fullPath, closeSidebar)
onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div class="al-shell">
    <!-- Backdrop mobile -->
    <button
      v-if="isSidebarOpen"
      class="al-backdrop"
      type="button"
      aria-label="Đóng menu quản trị"
      @click="closeSidebar"
    />

    <!-- ══════════ SIDEBAR ══════════ -->
    <aside id="admin-sidebar" class="al-sidebar" :class="{ 'is-open': isSidebarOpen }">
      <!-- Brand -->
      <RouterLink class="al-brand" to="/quan-tri" @click="closeSidebar">
        <span class="al-brand__icon">
          <img src="/assets/figma/home/icon-brand.svg" alt="" />
        </span>
        <span class="al-brand__text">
          <strong>LÂM ĐỒNG OCOP</strong>
          <small>Khu vực quản trị</small>
        </span>
      </RouterLink>

      <!-- Nav -->
      <nav class="al-nav" aria-label="Điều hướng quản trị">
        <span class="al-nav__section-label">MENU CHÍNH</span>
        <template v-for="item in navigation" :key="item.label">
          <RouterLink
            v-if="item.available"
            class="al-nav__item"
            :to="item.to"
            @click="closeSidebar"
          >
            <span class="al-nav__icon"><AppIcon :name="item.icon" :size="17" /></span>
            <span>{{ item.label }}</span>
          </RouterLink>
          <button v-else class="al-nav__item is-disabled" type="button" disabled :title="`${item.label} — sắp triển khai`">
            <span class="al-nav__icon"><AppIcon :name="item.icon" :size="17" /></span>
            <span>{{ item.label }}</span>
            <span class="al-nav__soon">Sắp có</span>
          </button>
        </template>
      </nav>

      <!-- Footer sidebar -->
      <div class="al-sidebar__footer">
        <div class="al-status-pill">
          <span class="al-status-dot" />
          <span>Hệ thống hoạt động</span>
        </div>
        <div class="al-footer-actions">
          <RouterLink class="al-footer-btn" to="/">
            <AppIcon name="arrowLeft" :size="14" />
            <span>Trang công khai</span>
          </RouterLink>
          <button class="al-footer-btn is-danger" type="button" @click="logout">
            <AppIcon name="logout" :size="14" />
            <span>Đăng xuất</span>
          </button>
        </div>
        <p class="al-version">Phiên bản 0.1.0</p>
      </div>
    </aside>

    <!-- ══════════ MAIN ══════════ -->
    <div class="al-main">
      <!-- Topbar -->
      <header class="al-topbar">
        <button
          class="al-topbar__toggle"
          type="button"
          :aria-expanded="isSidebarOpen"
          aria-controls="admin-sidebar"
          aria-label="Mở hoặc đóng menu quản trị"
          @click="isSidebarOpen = !isSidebarOpen"
        >
          <AppIcon name="menu" :size="20" />
        </button>

        <div class="al-topbar__title">
          <span class="al-topbar__breadcrumb">Hệ thống quản lý OCOP</span>
          <strong>{{ pageTitle }}</strong>
        </div>

        <div class="al-topbar__right">
          <!-- API health pill -->
          <span class="al-api-pill">
            <span class="al-api-dot" />
            <span class="al-api-label">API</span>
          </span>

          <!-- Avatar -->
          <RouterLink class="al-avatar" to="/tai-khoan">
            <span class="al-avatar__initial">{{ userInitial }}</span>
            <span class="al-avatar__info">
              <strong>{{ authStore.currentUser.value?.full_name }}</strong>
              <small>Quản trị viên</small>
            </span>
          </RouterLink>
        </div>
      </header>

      <!-- Content -->
      <div class="al-content">
        <RouterView />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ── Shell ── */
.al-shell {
  display: grid;
  min-height: 100vh;
  grid-template-columns: var(--admin-sidebar-width) minmax(0, 1fr);
  background: var(--admin-bg);
  font-family: var(--admin-font);
  color: var(--admin-text);
}

/* ── Backdrop mobile ── */
.al-backdrop {
  position: fixed;
  z-index: 45;
  inset: 0;
  border: 0;
  background: rgba(30, 42, 71, 0.48);
  backdrop-filter: blur(2px);
}

/* ══════════════ SIDEBAR ══════════════ */
.al-sidebar {
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
.al-sidebar::-webkit-scrollbar { display: none; }

/* Brand */
.al-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px 18px;
  border-bottom: 1px solid rgba(232, 237, 248, 0.10);
  color: #fff;
  text-decoration: none;
}
.al-brand__icon {
  display: grid;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 10px;
  background: rgba(47, 107, 255, 0.30);
}
.al-brand__icon img { width: 20px; height: 20px; }
.al-brand__text { display: grid; }
.al-brand__text strong {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.01em;
}
.al-brand__text small {
  font-size: 11px;
  color: var(--admin-muted-on-dark);
  margin-top: 1px;
}

/* Nav */
.al-nav {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 2px;
  margin-top: 20px;
}
.al-nav__section-label {
  padding: 0 10px 6px;
  color: var(--admin-muted-on-dark);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
}
.al-nav__item {
  display: flex;
  min-height: 40px;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border: 1px solid transparent;
  border-radius: var(--admin-radius-md);
  background: transparent;
  color: rgba(232, 237, 248, 0.70);
  font-size: var(--admin-font-sm);
  font-weight: 600;
  text-align: left;
  text-decoration: none;
  transition: background var(--admin-transition), color var(--admin-transition);
  cursor: pointer;
}
.al-nav__item:hover {
  background: var(--admin-sidebar-hover);
  color: #fff;
}
.al-nav__item.router-link-exact-active {
  background: var(--admin-primary-soft);
  color: var(--admin-primary);
  font-weight: 700;
}
.al-nav__item.router-link-exact-active .al-nav__icon {
  color: var(--admin-primary);
}
.al-nav__icon {
  display: grid;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 8px;
  background: rgba(232, 237, 248, 0.08);
  color: rgba(232, 237, 248, 0.55);
  transition: color var(--admin-transition);
}
.al-nav__item:hover .al-nav__icon {
  background: rgba(47, 107, 255, 0.18);
  color: #fff;
}
.al-nav__item.is-disabled {
  cursor: not-allowed;
  opacity: 0.45;
}
.al-nav__soon {
  margin-left: auto;
  padding: 2px 7px;
  border-radius: var(--admin-radius-pill);
  background: rgba(232, 237, 248, 0.12);
  color: var(--admin-muted-on-dark);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

/* Sidebar footer */
.al-sidebar__footer {
  margin-top: auto;
  padding-top: 14px;
  border-top: 1px solid rgba(232, 237, 248, 0.10);
}
.al-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: var(--admin-radius-pill);
  background: rgba(16, 185, 129, 0.15);
  color: #6ee7b7;
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 10px;
}
.al-status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10B981;
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.30);
  animation: al-pulse 2.4s ease-in-out infinite;
}
@keyframes al-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.al-footer-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}
.al-footer-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 8px 6px;
  border: 1px solid rgba(232, 237, 248, 0.14);
  border-radius: var(--admin-radius-sm);
  background: transparent;
  color: var(--admin-text-on-dark);
  font-size: 11px;
  font-weight: 600;
  text-align: center;
  text-decoration: none;
  cursor: pointer;
  transition: background var(--admin-transition);
}
.al-footer-btn:hover { background: rgba(232, 237, 248, 0.08); }
.al-footer-btn.is-danger { color: #fca5a5; }
.al-footer-btn.is-danger:hover { background: rgba(239, 68, 68, 0.12); border-color: rgba(239, 68, 68, 0.24); }
.al-version {
  margin: 8px 0 0;
  text-align: center;
  color: var(--admin-muted-on-dark);
  font-size: 10px;
}

/* ══════════════ MAIN ══════════════ */
.al-main { min-width: 0; }

/* Topbar */
.al-topbar {
  position: sticky;
  z-index: 30;
  top: 0;
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
.al-topbar__toggle {
  display: none;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  place-items: center;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-card);
  color: var(--admin-text);
  cursor: pointer;
}
.al-topbar__title { display: grid; }
.al-topbar__breadcrumb {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--admin-muted);
}
.al-topbar__title strong {
  font-size: var(--admin-font-lg);
  font-weight: 700;
  color: var(--admin-text);
}
.al-topbar__right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

/* API health pill */
.al-api-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: var(--admin-radius-pill);
  background: #D1FAE5;
  font-size: 12px;
  font-weight: 700;
  color: #065F46;
}
.al-api-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10B981;
}
.al-api-label::before { content: 'API kết nối'; }

/* Avatar */
.al-avatar {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 5px;
  border-radius: var(--admin-radius-md);
  color: var(--admin-text);
  text-decoration: none;
  transition: background var(--admin-transition);
}
.al-avatar:hover { background: var(--admin-primary-soft); }
.al-avatar__initial {
  display: grid;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 50%;
  background: var(--admin-primary);
  color: #fff;
  font-size: 13px;
  font-weight: 800;
}
.al-avatar__info { display: grid; }
.al-avatar__info strong {
  max-width: 150px;
  overflow: hidden;
  font-size: var(--admin-font-sm);
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--admin-text);
}
.al-avatar__info small {
  font-size: 11px;
  color: var(--admin-muted);
}

/* Content */
.al-content {
  width: min(100%, 1280px);
  margin-inline: auto;
  padding: 28px;
}

/* ══════════════ RESPONSIVE ══════════════ */
@media (max-width: 991.98px) {
  .al-shell { grid-template-columns: 1fr; }

  .al-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    width: min(var(--admin-sidebar-width), 85vw);
    transform: translateX(-110%);
    transition: transform 220ms cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: var(--admin-shadow-modal);
  }
  .al-sidebar.is-open { transform: translateX(0); }

  .al-topbar__toggle { display: grid; }
  .al-avatar__info { display: none; }
}

@media (max-width: 575.98px) {
  .al-topbar { padding-inline: 16px; }
  .al-api-label::before { content: 'API'; }
  .al-content { padding: 20px 16px; }
}
</style>
