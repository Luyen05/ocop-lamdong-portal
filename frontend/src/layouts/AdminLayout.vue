<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

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
  { label: 'Tổng quan', symbol: '▦', to: '/quan-tri', available: true },
  { label: 'Sản phẩm', symbol: '◈', to: '', available: false },
  { label: 'Điểm du lịch', symbol: '⌖', to: '', available: false },
  { label: 'Chủ thể / HTX', symbol: '♢', to: '/quan-tri/ho-so-chu-the', available: true },
  { label: 'Người dùng', symbol: '♙', to: '', available: false },
  { label: 'Đánh giá', symbol: '★', to: '', available: false },
  { label: 'Bài viết', symbol: '▤', to: '', available: false },
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
            <span aria-hidden="true">{{ item.symbol }}</span>
            {{ item.label }}
          </RouterLink>
          <button v-else type="button" disabled :title="`${item.label} sẽ được triển khai ở commit sau`">
            <span aria-hidden="true">{{ item.symbol }}</span>
            {{ item.label }}
            <small>Sắp phát triển</small>
          </button>
        </template>
      </nav>

      <div class="sidebar-footer">
        <RouterLink to="/">← Về trang công khai</RouterLink>
        <button type="button" @click="logout">Đăng xuất</button>
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
          ☰
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
  background: #f3f6f8;
}

.admin-sidebar {
  position: sticky;
  z-index: 40;
  top: 0;
  display: flex;
  height: 100vh;
  padding: 20px 16px;
  flex-direction: column;
  background: #101a30;
  color: #cbd5e1;
}

.admin-brand {
  display: flex;
  padding: 0 8px 20px;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid rgb(148 163 184 / 14%);
  color: #fff;
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
  color: #8290a6;
  font-size: 10px;
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
  padding: 10px 12px;
  align-items: center;
  gap: 10px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: #aab6c8;
  font-size: 12px;
  font-weight: 650;
  text-align: left;
  text-decoration: none;
}

.admin-nav a > span,
.admin-nav button > span {
  display: grid;
  width: 22px;
  place-items: center;
  color: #6ee7b7;
  font-size: 16px;
}

.admin-nav a:hover,
.admin-nav a.router-link-exact-active {
  border-color: rgb(52 211 153 / 18%);
  background: rgb(0 122 85 / 22%);
  color: #fff;
}

.admin-nav button {
  cursor: not-allowed;
  opacity: 0.58;
}

.admin-nav button small {
  margin-left: auto;
  color: #64748b;
  font-size: 8px;
  text-transform: uppercase;
}

.sidebar-footer {
  display: grid;
  margin-top: auto;
  padding-top: 16px;
  gap: 8px;
  border-top: 1px solid rgb(148 163 184 / 14%);
}

.sidebar-footer a,
.sidebar-footer button {
  padding: 9px 10px;
  border: 1px solid rgb(148 163 184 / 18%);
  border-radius: 9px;
  background: transparent;
  color: #cbd5e1;
  font-size: 11px;
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
  padding: 12px 28px;
  align-items: center;
  gap: 14px;
  border-bottom: 1px solid var(--ocop-border);
  background: rgb(255 255 255 / 94%);
  backdrop-filter: blur(12px);
}

.admin-topbar > div {
  display: grid;
}

.topbar-label {
  color: var(--ocop-slate);
  font-size: 10px;
  text-transform: uppercase;
}

.admin-topbar > div strong {
  color: var(--ocop-navy);
  font-size: 16px;
}

.sidebar-toggle {
  display: none;
  width: 38px;
  height: 38px;
  border: 1px solid var(--ocop-border);
  border-radius: 9px;
  background: #fff;
  color: var(--ocop-primary-900);
}

.admin-account {
  display: flex;
  margin-left: auto;
  align-items: center;
  gap: 8px;
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
  color: #fff;
  font-size: 13px;
  font-weight: 800;
}

.admin-account > span:last-child {
  display: grid;
}

.admin-account strong {
  max-width: 180px;
  overflow: hidden;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admin-account small {
  color: var(--ocop-slate);
  font-size: 10px;
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
    transition: transform 180ms ease;
  }

  .admin-sidebar.open {
    transform: translateX(0);
  }

  .sidebar-toggle {
    display: block;
  }

  .sidebar-backdrop {
    position: fixed;
    z-index: 35;
    inset: 0;
    display: block;
    border: 0;
    background: rgb(15 23 43 / 52%);
  }
}

@media (max-width: 575.98px) {
  .admin-topbar {
    padding-inline: 16px;
  }

  .topbar-label,
  .admin-account > span:last-child {
    display: none;
  }

  .admin-content {
    padding: 20px 16px;
  }
}
</style>
