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
  { label: 'Điểm du lịch', icon: 'map-pin', to: '', available: false },
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
  <div class="admin-shell">
    <aside id="admin-sidebar" class="admin-sidebar" :class="{ open: isSidebarOpen }">
      <RouterLink class="admin-brand" to="/quan-tri" @click="closeSidebar">
        <span class="brand-icon">
          <img src="/assets/figma/home/icon-brand.svg" alt="" />
        </span>
        <span>
          <strong>LÂM ĐỒNG OCOP</strong>
          <small>Khu vực quản trị</small>
        </span>
      </RouterLink>

      <nav class="admin-nav" aria-label="Điều hướng quản trị">
        <template v-for="item in navigation" :key="item.label">
          <RouterLink v-if="item.available" :to="item.to" @click="closeSidebar">
            <span aria-hidden="true"><AppIcon :name="item.icon" :size="18" /></span>
            {{ item.label }}
          </RouterLink>
          <button v-else type="button" disabled :title="`${item.label} sẽ được triển khai ở commit sau`">
            <span aria-hidden="true"><AppIcon :name="item.icon" :size="18" /></span>
            {{ item.label }}
            <small>Sắp phát triển</small>
          </button>
        </template>
      </nav>

      <div class="sidebar-footer">
        <RouterLink to="/"><AppIcon name="arrowLeft" :size="15" /> Về trang công khai</RouterLink>
        <button type="button" @click="logout"><AppIcon name="logout" :size="15" /> Đăng xuất</button>
      </div>
    </aside>

    <button
      v-if="isSidebarOpen"
      class="sidebar-backdrop"
      type="button"
      aria-label="Đóng menu quản trị"
      @click="closeSidebar"
    />

    <div class="admin-main">
      <header class="admin-topbar">
        <button
          class="sidebar-toggle"
          type="button"
          :aria-expanded="isSidebarOpen"
          aria-controls="admin-sidebar"
          aria-label="Mở hoặc đóng menu quản trị"
          @click="isSidebarOpen = !isSidebarOpen"
        >
          <AppIcon name="menu" :size="20" />
        </button>
        <div>
          <span class="topbar-label">Hệ thống quản lý OCOP</span>
          <strong>{{ pageTitle }}</strong>
        </div>
        <RouterLink class="admin-account" to="/tai-khoan">
          <span>{{ userInitial }}</span>
          <span>
            <strong>{{ authStore.currentUser.value?.full_name }}</strong>
            <small>Quản trị viên</small>
          </span>
        </RouterLink>
      </header>

      <div class="admin-content">
        <RouterView />
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-shell {
  display: grid;
  min-height: 100vh;
  grid-template-columns: 260px minmax(0, 1fr);
  background: var(--ocop-surface);
}

.admin-sidebar {
  position: sticky;
  z-index: 40;
  top: 0;
  display: flex;
  height: 100vh;
  padding: var(--ocop-space-5) var(--ocop-space-4);
  flex-direction: column;
  background: var(--ocop-sidebar);
  color: var(--ocop-sidebar-muted);
}

.admin-brand {
  display: flex;
  padding: 0 var(--ocop-space-2) var(--ocop-space-5);
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid color-mix(in srgb, var(--ocop-neutral-400) 14%, transparent);
  color: var(--ocop-white);
  text-decoration: none;
}

.brand-icon {
  display: grid;
  width: 38px;
  height: 38px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 10px;
  background: var(--ocop-primary-700);
}

.brand-icon img {
  width: 22px;
  height: 22px;
}

.admin-brand > span:last-child {
  display: grid;
}

.admin-brand strong {
  font-size: 14px;
}

.admin-brand small {
  margin-top: 2px;
  color: var(--ocop-sidebar-muted);
  font-size: var(--ocop-font-size-xs);
}

.admin-nav {
  display: grid;
  margin-top: 22px;
  gap: 5px;
}

.admin-nav a,
.admin-nav button {
  display: flex;
  min-height: 42px;
  padding: 10px var(--ocop-space-3);
  align-items: center;
  gap: 10px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: var(--ocop-sidebar-muted);
  font-size: var(--ocop-font-size-small);
  font-weight: 650;
  text-align: left;
  text-decoration: none;
}

.admin-nav a > span,
.admin-nav button > span {
  display: grid;
  width: 22px;
  place-items: center;
  color: var(--ocop-mint-300);
  font-size: var(--ocop-font-size-body-lg);
}

.admin-nav a:hover,
.admin-nav a.router-link-exact-active {
  border-color: color-mix(in srgb, var(--ocop-mint) 24%, transparent);
  background: color-mix(in srgb, var(--ocop-primary-500) 22%, transparent);
  color: var(--ocop-white);
}

.admin-nav button {
  cursor: not-allowed;
  opacity: 0.58;
}

.admin-nav button small {
  margin-left: auto;
  color: var(--ocop-neutral-500);
  font-size: 8px;
  text-transform: uppercase;
}

.sidebar-footer {
  display: grid;
  margin-top: auto;
  padding-top: var(--ocop-space-4);
  gap: var(--ocop-space-2);
  border-top: 1px solid color-mix(in srgb, var(--ocop-neutral-400) 14%, transparent);
}

.sidebar-footer a,
.sidebar-footer button {
  display: flex;
  padding: 9px 10px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border: 1px solid color-mix(in srgb, var(--ocop-neutral-400) 18%, transparent);
  border-radius: 9px;
  background: transparent;
  color: var(--ocop-text-on-dark);
  font-size: var(--ocop-font-size-caption);
  font-weight: 650;
  text-align: center;
  text-decoration: none;
}

.admin-main {
  min-width: 0;
}

.admin-topbar {
  position: sticky;
  z-index: 30;
  top: 0;
  display: flex;
  min-height: 72px;
  padding: var(--ocop-space-3) 28px;
  align-items: center;
  gap: 14px;
  border-bottom: 1px solid var(--ocop-border);
  background: color-mix(in srgb, var(--ocop-white) 94%, transparent);
  backdrop-filter: blur(12px);
}

.admin-topbar > div {
  display: grid;
}

.topbar-label {
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-xs);
  text-transform: uppercase;
}

.admin-topbar > div strong {
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-body-lg);
}

.sidebar-toggle {
  display: none;
  width: 38px;
  height: 38px;
  border: 1px solid var(--ocop-border);
  border-radius: 9px;
  background: var(--ocop-card);
  color: var(--ocop-primary-900);
  place-items: center;
}

.admin-account {
  display: flex;
  margin-left: auto;
  align-items: center;
  gap: var(--ocop-space-2);
  color: var(--ocop-navy);
  text-decoration: none;
}

.admin-account > span:first-child {
  display: grid;
  width: 36px;
  height: 36px;
  place-items: center;
  border-radius: 50%;
  background: var(--ocop-primary-700);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-small);
  font-weight: 800;
}

.admin-account > span:last-child {
  display: grid;
}

.admin-account strong {
  max-width: 180px;
  overflow: hidden;
  font-size: var(--ocop-font-size-caption);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admin-account small {
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-2xs);
}

.admin-content {
  width: min(100%, 1280px);
  margin-inline: auto;
  padding: 28px;
}

.sidebar-backdrop {
  display: none;
}

@media (max-width: 991.98px) {
  .admin-shell {
    grid-template-columns: 1fr;
  }

  .admin-sidebar {
    position: fixed;
    left: 0;
    width: min(280px, 86vw);
    transform: translateX(-105%);
    transition: transform var(--ocop-transition);
  }

  .admin-sidebar.open {
    transform: translateX(0);
  }

  .sidebar-toggle {
    display: grid;
  }

  .sidebar-backdrop {
    position: fixed;
    z-index: 35;
    inset: 0;
    display: block;
    border: 0;
    background: color-mix(in srgb, var(--ocop-neutral-900) 52%, transparent);
  }
}

@media (max-width: 575.98px) {
  .admin-topbar {
    padding-inline: var(--ocop-space-4);
  }

  .topbar-label,
  .admin-account > span:last-child {
    display: none;
  }

  .admin-content {
    padding: var(--ocop-space-5) var(--ocop-space-4);
  }
}
</style>
