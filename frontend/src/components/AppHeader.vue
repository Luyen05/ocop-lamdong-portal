<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppIcon from '@/components/ui/AppIcon.vue'
import { authStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const currentUser = authStore.currentUser
const isAuthenticated = authStore.isAuthenticated
const isMenuOpen = ref(false)
const headerSearch = ref('')

const roleLabel = computed(() => {
  const labels = {
    admin: 'Quản trị viên',
    subject: 'Chủ thể OCOP',
    user: 'Người dùng',
  }
  return currentUser.value ? labels[currentUser.value.role] : ''
})

const userInitial = computed(() => currentUser.value?.full_name.trim().charAt(0).toUpperCase() || 'U')

const publicNavigation = [
  { label: 'Trang chủ', to: '/', icon: 'home' },
  { label: 'Sản phẩm OCOP', to: '/san-pham', icon: 'package' },
  { label: 'Điểm du lịch', to: '/#diem-du-lich', icon: 'map-pin' },
  { label: 'Bản đồ số GIS', to: '/#ban-do', icon: 'map' },
  { label: 'Tin tức', to: '/#tin-tuc', icon: 'newspaper' },
]

const navigation = computed(() => [
  ...publicNavigation,
  ...(currentUser.value?.role === 'user' || currentUser.value?.role === 'subject'
    ? [{
        label: currentUser.value.role === 'subject' ? 'Quản lý sản phẩm' : 'Đăng ký chủ thể',
        to: currentUser.value.role === 'subject' ? '/chu-the/san-pham' : '/dang-ky-chu-the',
        icon: currentUser.value.role === 'subject' ? 'package' : 'building',
      }]
    : []),
  ...(currentUser.value?.role === 'admin'
    ? [{ label: 'Quản trị', to: '/quan-tri', icon: 'dashboard' }]
    : []),
])

function asset(name: string): string {
  return `/assets/figma/home/${name}`
}

function closeMenu(): void {
  isMenuOpen.value = false
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') closeMenu()
}

async function submitHeaderSearch(): Promise<void> {
  const search = headerSearch.value.trim()
  await router.push({ name: 'products', query: search ? { search } : {} })
  closeMenu()
}

async function logout(): Promise<void> {
  authStore.logout()
  closeMenu()
  await router.push('/')
}

watch(() => route.fullPath, closeMenu)
onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <header class="site-header">
    <div class="announcement-bar">
      <div class="site-container announcement-inner">
        <p>
          <span class="online-dot" aria-hidden="true" />
          Cổng thông tin quảng bá nông sản OCOP &amp; bản đồ số du lịch nông nghiệp tỉnh Lâm Đồng
        </p>
        <div class="announcement-actions">
          <span class="capstone-label">
            <AppIcon name="shieldCheck" :size="14" />
            Dữ liệu OCOP được kiểm duyệt
          </span>
          <span>Hotline: 0263.3822000</span>
        </div>
      </div>
    </div>

    <div class="main-header">
      <div class="site-container header-inner">
        <RouterLink class="site-brand" to="/" aria-label="Lâm Đồng OCOP - Trang chủ">
          <span class="brand-symbol">
            <img :src="asset('icon-brand.svg')" alt="" />
          </span>
          <span class="brand-copy">
            <span class="brand-title">
              <strong>LÂM ĐỒNG OCOP</strong>
              <small>GIS Map</small>
            </span>
            <span>Nông sản OCOP &amp; Du lịch Nông nghiệp</span>
          </span>
        </RouterLink>

        <form class="header-search" role="search" @submit.prevent="submitHeaderSearch">
          <AppIcon name="search" :size="16" />
          <input
            v-model="headerSearch"
            type="search"
            aria-label="Tìm kiếm sản phẩm"
            placeholder="Tìm sản phẩm OCOP..."
          />
        </form>

        <button
          class="menu-toggle"
          type="button"
          :aria-expanded="isMenuOpen"
          aria-controls="main-navigation"
          aria-label="Mở hoặc đóng menu"
          @click="isMenuOpen = !isMenuOpen"
        >
          <AppIcon name="menu" :size="22" />
        </button>

        <div id="main-navigation" class="navigation-panel" :class="{ open: isMenuOpen }">
          <nav class="main-nav" aria-label="Điều hướng chính">
            <RouterLink v-for="item in navigation" :key="item.label" :to="item.to" @click="closeMenu">
              <AppIcon :name="item.icon" :size="15" />
              <span>{{ item.label }}</span>
            </RouterLink>
          </nav>

          <div v-if="isAuthenticated" class="account-actions">
            <RouterLink class="user-link" to="/tai-khoan" @click="closeMenu">
              <span class="user-avatar">{{ userInitial }}</span>
              <span class="user-copy">
                <small>{{ roleLabel }}</small>
                <strong>{{ currentUser?.full_name }}</strong>
              </span>
            </RouterLink>
            <button class="logout-button" type="button" @click="logout">
              <AppIcon name="logout" :size="14" /> Đăng xuất
            </button>
          </div>
          <div v-else class="account-actions guest-actions">
            <RouterLink to="/dang-nhap" @click="closeMenu">Đăng nhập</RouterLink>
            <RouterLink class="register-button" to="/dang-ky" @click="closeMenu">Đăng ký</RouterLink>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.site-header {
  position: sticky;
  z-index: 100;
  top: 0;
  border-bottom: 1px solid var(--ocop-border);
  background: rgb(255 255 255 / 96%);
  box-shadow: 0 1px 1px rgb(0 0 0 / 5%);
  backdrop-filter: blur(14px);
}

.announcement-bar {
  min-height: 28px;
  padding: 6px 0;
  background: var(--ocop-primary-950);
  color: #cdebd9;
  font-size: 12px;
}

.announcement-inner,
.announcement-inner p,
.announcement-actions,
.capstone-label {
  display: flex;
  align-items: center;
}

.announcement-inner {
  justify-content: space-between;
  gap: 16px;
}

.announcement-inner p {
  gap: 8px;
  margin: 0;
  color: #e3f4ea;
  font-weight: 500;
}

.online-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: var(--ocop-mint);
}

.announcement-actions {
  flex: 0 0 auto;
  gap: 16px;
}

.capstone-label {
  gap: 5px;
  padding: 2px 10px;
  border: 1px solid rgb(102 201 150 / 42%);
  border-radius: var(--ocop-radius-xs);
  background: rgb(18 55 42 / 72%);
}

.main-header {
  background: var(--ocop-card);
}

.header-inner {
  position: relative;
  display: flex;
  min-height: 72px;
  align-items: center;
  gap: 16px;
}

.site-brand,
.user-link {
  display: inline-flex;
  align-items: center;
  color: var(--ocop-navy);
  text-decoration: none;
}

.site-brand {
  min-width: 248px;
  gap: 12px;
}

.brand-symbol {
  display: grid;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-primary-700);
  box-shadow: 0 4px 8px rgb(30 113 79 / 22%);
}

.brand-symbol img {
  width: 24px;
  height: 24px;
}

.brand-copy {
  display: grid;
  color: var(--ocop-slate);
  font-size: 13px;
  font-weight: 500;
  line-height: 16px;
}

.brand-title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.brand-title strong {
  color: var(--ocop-navy);
  font-size: 16px;
  letter-spacing: -0.4px;
}

.brand-title small {
  padding: 2px 6px;
  border: 1px solid #e9c36d;
  border-radius: var(--ocop-radius-xs);
  background: var(--ocop-warning-soft);
  color: var(--ocop-warning);
  font-size: 10px;
  font-weight: 700;
  line-height: 12px;
}

.header-search {
  position: relative;
  display: none;
  min-width: 0;
  flex: 1 1 180px;
  max-width: 220px;
}

.header-search .app-icon {
  position: absolute;
  top: 50%;
  left: 12px;
  transform: translateY(-50%);
  color: var(--ocop-slate);
}

.header-search input {
  width: 100%;
  height: 36px;
  padding: 6px 12px 6px 36px;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-sm);
  outline: 0;
  background: rgb(238 243 239 / 82%);
  color: var(--ocop-navy);
  font-size: 12px;
}

.header-search input:focus {
  border-color: var(--ocop-primary-500);
  box-shadow: 0 0 0 3px rgb(30 113 79 / 12%);
}

.navigation-panel,
.main-nav,
.account-actions,
.user-copy {
  display: flex;
  align-items: center;
}

.navigation-panel {
  min-width: 0;
  flex: 1;
  justify-content: flex-end;
  gap: 8px;
}

.main-nav {
  gap: 2px;
}

.main-nav a {
  display: flex;
  min-width: 64px;
  min-height: 40px;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 7px 8px;
  border: 1px solid transparent;
  border-radius: var(--ocop-radius-sm);
  color: var(--ocop-slate);
  font-size: 13px;
  font-weight: 650;
  line-height: 14px;
  text-align: center;
  text-decoration: none;
}

.main-nav a:hover,
.main-nav a.router-link-active {
  border-color: var(--ocop-mint-border);
  background: var(--ocop-mint-soft);
  color: var(--ocop-primary-900);
}

.account-actions {
  flex: 0 0 auto;
  gap: 6px;
}

.user-link {
  max-width: 160px;
  gap: 8px;
  padding: 5px 8px;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-surface);
}

.user-avatar {
  display: grid;
  width: 28px;
  height: 28px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  background: var(--ocop-primary-700);
  color: #fff;
  font-size: 12px;
  font-weight: 800;
}

.user-copy {
  min-width: 0;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.15;
}

.user-copy small,
.user-copy strong {
  overflow: hidden;
  max-width: 104px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-copy small {
  color: var(--ocop-text-tertiary);
  font-size: 11px;
  text-transform: uppercase;
}

.user-copy strong {
  color: var(--ocop-navy);
  font-size: 12px;
}

.logout-button,
.guest-actions a {
  border: 0;
  background: transparent;
  color: var(--ocop-primary-900);
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
}

.logout-button {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 7px;
}

.guest-actions .register-button {
  padding: 8px 12px;
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-primary-700);
  color: #fff;
}

.menu-toggle {
  display: none;
  width: 40px;
  height: 40px;
  margin-left: auto;
  padding: 0;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-card);
  align-items: center;
  justify-content: center;
  color: var(--ocop-primary-950);
}

@media (min-width: 1320px) {
  .header-search {
    display: block;
  }
}

@media (max-width: 1199.98px) {
  .announcement-inner p {
    overflow: hidden;
    max-width: 58%;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .menu-toggle {
    display: inline-flex;
  }

  .navigation-panel {
    position: absolute;
    top: calc(100% + 1px);
    right: 0;
    left: 0;
    display: none;
    max-height: calc(100vh - 96px);
    align-items: stretch;
    padding: 16px;
    overflow-y: auto;
    border-bottom: 1px solid var(--ocop-border);
    background: var(--ocop-card);
    box-shadow: 0 18px 30px rgb(15 23 43 / 12%);
  }

  .navigation-panel.open,
  .main-nav {
    display: grid;
  }

  .navigation-panel.open {
    gap: 12px;
  }

  .main-nav {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .main-nav a {
    justify-content: flex-start;
    padding: 10px 12px;
    text-align: left;
  }

  .account-actions {
    justify-content: flex-end;
    padding-top: 12px;
    border-top: 1px solid var(--ocop-border);
  }
}

@media (max-width: 767.98px) {
  .announcement-bar {
    min-height: 24px;
    padding: 5px 0;
  }

  .announcement-inner {
    justify-content: center;
  }

  .announcement-inner p {
    max-width: 100%;
    font-size: 10px;
  }

  .announcement-actions {
    display: none;
  }

  .header-inner {
    min-height: 62px;
  }

  .site-brand {
    min-width: 0;
  }

  .brand-symbol {
    width: 36px;
    height: 36px;
  }

  .brand-title strong {
    font-size: 14px;
  }

  .brand-copy > span:last-child,
  .brand-title small {
    display: none;
  }
}
</style>
