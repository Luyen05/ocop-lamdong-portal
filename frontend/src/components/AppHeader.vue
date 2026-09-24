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
const isSearchOpen = ref(false)
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
  { label: 'Khám phá Lâm Đồng', to: '/diem-du-lich', icon: 'map-pin' },
  { label: 'Bản đồ', to: '/ban-do', icon: 'map' },
  { label: 'Tin tức', to: '/tin-tuc', icon: 'newspaper' },
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

function closeSearch(): void {
  isSearchOpen.value = false
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') closeMenu()
}

async function submitHeaderSearch(): Promise<void> {
  const search = headerSearch.value.trim()
  await router.push({ name: 'products', query: search ? { search } : {} })
  closeMenu()
  closeSearch()
}

async function logout(): Promise<void> {
  authStore.logout()
  closeMenu()
  await router.push('/')
}

watch(() => route.fullPath, () => {
  closeMenu()
  closeSearch()
})
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
              <small>Cổng thông tin</small>
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
          class="search-toggle"
          type="button"
          :aria-expanded="isSearchOpen"
          aria-controls="responsive-header-search"
          aria-label="Mở hoặc đóng tìm kiếm sản phẩm"
          @click="isSearchOpen = !isSearchOpen"
        >
          <AppIcon name="search" :size="18" />
        </button>

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

      <form
        v-if="isSearchOpen"
        id="responsive-header-search"
        class="responsive-search site-container"
        role="search"
        @submit.prevent="submitHeaderSearch"
      >
        <AppIcon name="search" :size="17" />
        <input
          v-model="headerSearch"
          type="search"
          aria-label="Tìm kiếm sản phẩm"
          placeholder="Nhập tên sản phẩm OCOP..."
          autofocus
        />
        <button type="submit">Tìm kiếm</button>
      </form>
    </div>
  </header>
</template>

<style scoped>
.site-header {
  position: sticky;
  z-index: 100;
  top: 0;
  border-bottom: 1px solid var(--ocop-border);
  background: color-mix(in srgb, var(--ocop-white) 96%, transparent);
  box-shadow: 0 1px 1px color-mix(in srgb, var(--ocop-black) 5%, transparent);
  backdrop-filter: blur(14px);
}

.announcement-bar {
  min-height: 28px;
  padding: 6px 0;
  background: var(--ocop-primary-950);
  color: var(--ocop-mint-100);
  font-size: var(--ocop-font-size-caption);
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
  gap: var(--ocop-space-4);
}

.announcement-inner p {
  gap: var(--ocop-space-2);
  margin: 0;
  color: var(--ocop-success-soft);
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
  gap: var(--ocop-space-4);
}

.capstone-label {
  gap: 5px;
  padding: 2px 10px;
  border: 1px solid color-mix(in srgb, var(--ocop-mint) 42%, transparent);
  border-radius: var(--ocop-radius-xs);
  background: color-mix(in srgb, var(--ocop-primary-950) 72%, transparent);
}

.main-header {
  background: var(--ocop-card);
}

.header-inner {
  position: relative;
  display: flex;
  min-height: 72px;
  align-items: center;
  gap: var(--ocop-space-4);
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
  gap: var(--ocop-space-3);
}

.brand-symbol {
  display: grid;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-primary-700);
  box-shadow: 0 4px 8px color-mix(in srgb, var(--ocop-primary-700) 22%, transparent);
}

.brand-symbol img {
  width: 24px;
  height: 24px;
}

.brand-copy {
  display: grid;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
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
  font-size: var(--ocop-font-size-body-lg);
  letter-spacing: -0.4px;
}

.brand-title small {
  padding: 2px 6px;
  border: 1px solid var(--ocop-gold-300);
  border-radius: var(--ocop-radius-xs);
  background: var(--ocop-warning-soft);
  color: var(--ocop-warning);
  font-size: var(--ocop-font-size-2xs);
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

.search-toggle {
  display: inline-flex;
  width: 40px;
  height: 40px;
  margin-left: auto;
  padding: 0;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-card);
  color: var(--ocop-primary-900);
}

.responsive-search {
  display: grid;
  padding-block: 10px;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 9px;
  border-top: 1px solid var(--ocop-border-soft);
}

.responsive-search input {
  min-width: 0;
  height: 40px;
  padding: var(--ocop-space-2) var(--ocop-space-3);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-sm);
  outline: 0;
}

.responsive-search input:focus {
  border-color: var(--ocop-primary-500);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ocop-primary-700) 12%, transparent);
}

.responsive-search button {
  min-height: 40px;
  padding: var(--ocop-space-2) 14px;
  border: 0;
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-primary-700);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
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
  padding: 6px var(--ocop-space-3) 6px 36px;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-sm);
  outline: 0;
  background: color-mix(in srgb, var(--ocop-surface-muted) 82%, transparent);
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-caption);
}

.header-search input:focus {
  border-color: var(--ocop-primary-500);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ocop-primary-700) 12%, transparent);
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
  gap: var(--ocop-space-2);
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
  padding: 7px var(--ocop-space-2);
  border: 1px solid transparent;
  border-radius: var(--ocop-radius-sm);
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
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
  gap: var(--ocop-space-2);
  padding: 5px var(--ocop-space-2);
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
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-caption);
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
  font-size: var(--ocop-font-size-xs);
  text-transform: uppercase;
}

.user-copy strong {
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-caption);
}

.logout-button,
.guest-actions a {
  border: 0;
  background: transparent;
  color: var(--ocop-primary-900);
  font-size: var(--ocop-font-size-caption);
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
  padding: var(--ocop-space-2) var(--ocop-space-3);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-primary-700);
  color: var(--ocop-white);
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

  .search-toggle,
  .responsive-search {
    display: none;
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
    margin-left: 0;
  }

  .navigation-panel {
    position: absolute;
    top: calc(100% + 1px);
    right: 0;
    left: 0;
    display: none;
    max-height: calc(100vh - 96px);
    align-items: stretch;
    padding: var(--ocop-space-4);
    overflow-y: auto;
    border-bottom: 1px solid var(--ocop-border);
    background: var(--ocop-card);
    box-shadow: 0 18px 30px color-mix(in srgb, var(--ocop-neutral-900) 12%, transparent);
  }

  .navigation-panel.open,
  .main-nav {
    display: grid;
  }

  .navigation-panel.open {
    gap: var(--ocop-space-3);
  }

  .main-nav {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .main-nav a {
    justify-content: flex-start;
    padding: 10px var(--ocop-space-3);
    text-align: left;
  }

  .account-actions {
    justify-content: flex-end;
    padding-top: var(--ocop-space-3);
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
    font-size: var(--ocop-font-size-2xs);
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

  .responsive-search {
    width: min(calc(100% - 2rem), var(--ocop-container));
    grid-template-columns: auto minmax(0, 1fr);
  }

  .responsive-search button {
    grid-column: 1 / -1;
  }
}
</style>
